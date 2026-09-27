import os

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


def _chat(system: str, user: str, base_url: str, api_key: str, model: str, tokens: int) -> str:
    from openai import OpenAI

    client = OpenAI(base_url=base_url, api_key=api_key, timeout=120)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        max_tokens=tokens,
    )
    return resp.choices[0].message.content


def answer_leaked(ans: str) -> bool:
    """Detecta razonamiento en voz alta que jamás debe ver el usuario."""
    t = (ans or "").lower()
    return any(m in t for m in (
        "thinking process", "analyze user input", "paso 1: analizar",
        "identify relevant information", "draft the answer",
    ))


def extractive(lang: str, context: str) -> str:
    first = context.split("\n")[0] if context else ""
    if lang == "es":
        return f"Basado en [1]: {first} [1]"
    return f"Based on [1]: {first} [1]"


def llm_answer(q: str, lang: str, context: str) -> str:
    sys = (
        f"Answer in {'Spanish' if lang == 'es' else 'English'}. "
        "Cite sources with [1][2]. Use only the context. "
        "Reply DIRECTLY with the final answer and its citations; "
        "do not show your reasoning process."
    )
    user = f"Q: {q}\nContext:\n{context}"
    nv = os.getenv("NVIDIA_API_KEY", "")
    rk = os.getenv("FREELLMAPI_API_KEY", "")
    if nv or rk:
        try:
            from src.fallback import call_with_fallback

            def primary():
                if not nv:
                    raise RuntimeError("sin NVIDIA_API_KEY")
                return _chat(sys, user, "https://integrate.api.nvidia.com/v1", nv,
                             os.getenv("NIM_CHAT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"), 1500)

            def fallback():
                if not rk:
                    raise RuntimeError("sin FREELLMAPI_API_KEY")
                return _chat(sys, user,
                             os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1"), rk,
                             os.getenv("FALLBACK_CHAT_MODEL", "gpt-oss-20b"), 1500)

            ans, who = call_with_fallback(primary, fallback, label="ask")
            print(f"ask servido por: {who}")
            if answer_leaked(ans):
                print("ask: reasoning filtrado, degrado a extractivo")
            else:
                return ans
        except Exception as e:
            print(f"ask LLMs no disponibles ({e.__class__.__name__}), sigo a OpenAI/extractivo")
    key = os.getenv("OPENAI_API_KEY", "")
    if key and not key.startswith("sk-change"):
        try:
            from openai import OpenAI

            client = OpenAI()
            model = os.getenv("LLM_MODEL", "gpt-4o-mini")
            sys = (
                f"Answer in {'Spanish' if lang == 'es' else 'English'}. "
                "Cite sources with [1][2]. Use only the context."
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": f"Q: {q}\nContext:\n{context}"},
                ],
                max_tokens=300,
            )
            ans = resp.choices[0].message.content
            if not answer_leaked(ans):
                return ans
            print("ask: reasoning filtrado (openai), degrado a extractivo")
        except Exception:
            pass
    # fallback extractivo (sin LLM, para test/offline)
    return extractive(lang, context)


@app.get("/ask")
def ask(q: str, lang: str = "es"):
    if lang not in ("es", "en"):
        lang = "es"
    col = f"docs_{lang}"
    client = get_client()
    qvec = embed([q])[0]
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
    context = "\n".join(f"[{i + 1}] {s['text']}" for i, s in enumerate(sources))
    return {"answer": llm_answer(q, lang, context), "sources": sources, "lang": lang}
