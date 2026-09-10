import os

from dotenv import load_dotenv
from fastapi import FastAPI

from src.embed import embed
from src.ingest import get_client

load_dotenv()
app = FastAPI(title="rag-wa-evals")


def llm_answer(q: str, lang: str, context: str) -> str:
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
