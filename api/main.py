import os

from dotenv import load_dotenv
from fastapi import FastAPI

from src.embed import embed
from src.ingest import get_client

load_dotenv()
app = FastAPI(title="rag-wa-evals")


def llm_answer(q: str, lang: str, context: str) -> str:
    nv = os.getenv("NVIDIA_API_KEY", "")
    if nv:
        try:
            from openai import OpenAI

            client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=nv,
                timeout=120,
            )
            model = os.getenv("NIM_CHAT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
            sys = (
                f"Answer in {'Spanish' if lang == 'es' else 'English'}. "
                "Cite sources with [1][2]. Use only the context. "
                "Reply DIRECTLY with the final answer and its citations; "
                "do not show your reasoning process."
            )
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": f"Q: {q}\nContext:\n{context}"},
                ],
                max_tokens=1500,
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"NIM falló ({e.__class__.__name__}), pruebo siguiente")
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
            return resp.choices[0].message.content
        except Exception:
            pass
    # fallback extractivo (sin LLM, para test/offline)
    first = context.split("\n")[0] if context else ""
    if lang == "es":
        return f"Basado en [1]: {first} [1]"
    return f"Based on [1]: {first} [1]"


@app.get("/ask")
def ask(q: str, lang: str = "es"):
    if lang not in ("es", "en"):
        lang = "es"
    col = f"docs_{lang}"
    client = get_client()
    qvec = embed([q])[0]
    try:
        from src.hybrid import hybrid_search

        sources = hybrid_search(client, lang, qvec, q)
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
