import os
import re
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.embed import embed
from src.ingest import get_client

load_dotenv()
app = FastAPI(title="rag-wa-evals")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="api/static"), name="static")


@app.get("/")
def home():
    return FileResponse("api/static/index.html")


_ASK_CACHE: dict = {}

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"\w{4,}")
_LEAK_MARKERS = (
    "thinking process", "analyze user input", "paso 1: analizar",
    "identify relevant information", "draft the answer",
    "count words", "let me count", "let's count",
    "scan context", "user asks", "document [",
)
_STEP = re.compile(r"(?m)^\s*\d+\.\s+\*\*")


def _looks_like_reasoning(t: str) -> bool:
    """Un tramo es razonamiento si coincide con los markers o es un paso numerado."""
    return answer_leaked(t) or bool(_STEP.search(t))


def _chat(system: str, user: str, base_url: str, api_key: str, model: str, tokens: int) -> str:
    from openai import OpenAI

    # max_retries=0: el cliente reintenta 2 veces por defecto y multiplicaba
    # el timeout (45s x3 = 135s medidos en Render)
    client = OpenAI(base_url=base_url, api_key=api_key,
                    timeout=float(os.getenv("LLM_TIMEOUT", "25")), max_retries=0)
    extra: dict = {}
    if "nvidia" in base_url:
        # nemotron razona en voz alta si no lo apagas explícitamente
        extra["extra_body"] = {"reasoning": {"effort": os.getenv("NIM_REASONING", "none")}}
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=tokens,
        **extra,
    )
    return resp.choices[0].message.content


def answer_leaked(ans: str) -> bool:
    """Detecta razonamiento en voz alta que jamás debe ver el usuario."""
    t = (ans or "").lower()
    return any(m in t for m in _LEAK_MARKERS)


def strip_reasoning(ans: str) -> str:
    """Salva el tramo final cuando el modelo filtró su razonamiento.

    Devuelve "" si todo el texto es razonamiento (entonces sí hay que degradar).
    """
    if not ans:
        return ""
    if not answer_leaked(ans):
        return ans
    m = re.search(r"(?im)^\s*\**\s*(final answer|answer|respuesta final|respuesta)\s*\**\s*[:：]\s*", ans)
    if m:
        tail = ans[m.end():].strip()
        if len(tail) >= 25:
            return tail
    for part in reversed(re.split(r"\n\s*\n", ans)):
        t = part.strip()
        if len(t) >= 25 and not _looks_like_reasoning(t):
            return t
    return ""


def _norm(text: str) -> str:
    """Quita el marcador "[n] " que viene del contexto y colapsa espacios."""
    return " ".join(re.sub(r"^\s*\[\d+\]\s*", "", text or "").split())


def _clip(text: str, limit: int = 400) -> str:
    """Corta en un límite de palabra: nunca a mitad de palabra."""
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:") + "…"


def extractive(lang: str, q: str, context: str) -> str:
    """Fallback sin LLM: frases del chunk top-1, priorizando las que solapan con la pregunta."""
    first = _norm(context.split("\n")[0] if context else "")
    sents = [s for s in _SENT_SPLIT.split(first) if s.strip()]
    terms = set(_WORD.findall((q or "").lower()))
    scored = [(len(terms & set(_WORD.findall(s.lower()))), s) for s in sents]
    picked = [s for sc, s in scored if sc > 0][:3] or sents[:2]
    body = _clip(" ".join(picked) if picked else first)
    head = "Según las fuentes" if lang == "es" else "According to the sources"
    return f"{head} [1]: {body} [1]"


def llm_candidates() -> list[tuple[str, str, str, str]]:
    """(nombre, base_url, api_key, modelo) en orden de preferencia para redactar."""
    out: list[tuple[str, str, str, str]] = []
    gk = os.getenv("GEMINI_API_KEY", "").strip()
    if gk:
        # gemini-2.5-flash: ~2s y estable; NIM cuelga hasta el timeout a veces
        out.append(("gemini", "https://generativelanguage.googleapis.com/v1beta/openai", gk,
                    os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")))
    gq = os.getenv("GROQ_API_KEY", "").strip()
    if gq:
        out.append(("groq", "https://api.groq.com/openai/v1", gq,
                    os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")))
    nv = os.getenv("NVIDIA_API_KEY", "").strip()
    if nv:
        out.append(("nim", "https://integrate.api.nvidia.com/v1", nv,
                    os.getenv("NIM_CHAT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")))
    rk = os.getenv("FREELLMAPI_API_KEY", "").strip()
    if rk:
        out.append(("router", os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1").strip(), rk,
                    os.getenv("FALLBACK_CHAT_MODEL", "gpt-oss-20b")))
    ok = os.getenv("OPENAI_API_KEY", "").strip()
    if ok and not ok.startswith("sk-change"):
        out.append(("openai", "https://api.openai.com/v1", ok,
                    os.getenv("LLM_MODEL", "gpt-4o-mini")))
    return out


def llm_answer(q: str, lang: str, context: str) -> str:
    sys = (
        f"Answer in {'Spanish' if lang == 'es' else 'English'}. "
        "Cite sources with [1][2]. Use only the context. "
        "Your FIRST line must be the final answer itself: "
        "no preamble, no thinking process, no numbered steps, no bullet lists. "
        "At most 120 words."
    )
    user = f"Q: {q}\nContext:\n{context}"
    tokens = int(os.getenv("ANSWER_MAX_TOKENS", "400"))
    for name, base, key, model in llm_candidates():
        try:
            ans = _chat(sys, user, base, key, model, tokens)
        except Exception as e:
            print(f"ask: {name} falló ({e.__class__.__name__}), pruebo el siguiente")
            continue
        clean = strip_reasoning(ans)
        if clean and not answer_leaked(clean):
            if clean != ans:
                print(f"ask: {name} filtró razonamiento, conservé la respuesta final")
            print(f"ask servido por: {name}")
            return clean
        print(f"ask: {name} devolvió solo razonamiento/vacío, pruebo el siguiente")
    # fallback extractivo (sin LLM, para test/offline)
    return extractive(lang, q, context)


@app.get("/ask")
def ask(q: str, lang: str = "en"):
    if lang not in ("es", "en"):
        lang = "en"
    key = (q.strip().lower(), lang)
    if key in _ASK_CACHE:
        print("ask: caché exacta")
        return _ASK_CACHE[key]
    col = f"docs_{lang}"
    t0 = time.perf_counter()
    client = get_client()
    qvec = embed([q])[0]
    t1 = time.perf_counter()
    try:
        from src.hybrid import hybrid_search
        from src.rerank import rerank

        cands = hybrid_search(client, lang, qvec, q, k_dense=10, k_bm25=10, k_final=20)
        sources = rerank(q, cands, top_n=5)
    except Exception as e:
        print(f"hybrid falló ({e.__class__.__name__}), fallback denso")
        hits = client.query_points(collection_name=col, query=qvec, limit=5).points
        sources = [
            {
                "text": h.payload.get("text", ""),
                "source": h.payload.get("source", ""),
                "score": h.score,
            }
            for h in hits
        ]
    t2 = time.perf_counter()
    context = "\n".join(f"[{i + 1}] {s['text']}" for i, s in enumerate(sources))
    answer = llm_answer(q, lang, context)
    t3 = time.perf_counter()
    out = {
        "answer": answer,
        "sources": sources,
        "lang": lang,
        "timing": {
            "embed": round(t1 - t0, 2),
            "search": round(t2 - t1, 2),
            "answer": round(t3 - t2, 2),
            "total": round(t3 - t0, 2),
        },
    }
    _ASK_CACHE[key] = out
    return out
