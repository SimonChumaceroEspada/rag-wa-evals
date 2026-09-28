"""Rerank listwise: reordena los top-20 (RRF) y deja top-5.

Scorer default: LLM vía router (gpt-oss-20b, rápido + JSON).
Si el scorer falla: fallback al orden RRF (nunca rompe /ask).
"""

import json
import os
import re


def llm_score_fn(q: str, docs: list[dict]) -> list[float]:
    from dotenv import load_dotenv

    load_dotenv()
    from openai import OpenAI

    base = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")
    key = os.getenv("FREELLMAPI_API_KEY", "")
    try:
        if not key:
            raise RuntimeError("sin router")
        return _score_with(base, key, os.getenv("RERANK_MODEL", "gpt-oss-20b"), q, docs)
    except Exception as e:
        print(f"rerank router falló ({e.__class__.__name__}), pruebo NIM directo")
        nv = os.getenv("NVIDIA_API_KEY", "")
        if not nv:
            raise
        return _score_with("https://integrate.api.nvidia.com/v1", nv,
                           os.getenv("NIM_CHAT_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b"),
                           q, docs)


def _score_with(base: str, key: str, model: str, q: str, docs: list[dict]) -> list[float]:
    from openai import OpenAI

    client = OpenAI(base_url=base, api_key=key, timeout=120)
    if not docs:
        return []
    bundle = "\n".join(
        f"[{i + 1}] {d['text'][:400]}" for i, d in enumerate(docs)
    )
    prompt = (
        "Rank these passages by relevance to QUESTION (most relevant first).\n"
        "Reply with ONLY a JSON list of numbers, e.g. [3, 1, 2].\n"
        f"QUESTION: {q}\nPASSAGES:\n{bundle}"
    )
    def ask(extra=""):
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You output ONLY a JSON list of numbers, never explanations, never thinking."},
                {"role": "user", "content": prompt + extra},
            ],
            max_tokens=300,
        )
        return r.choices[0].message.content or ""

    raw = ask()
    m = re.search(r"\[[\d,\s]+\]", raw)
    if m is None:  # reintento único ante divague
        raw = ask("\nReply NOW with only the list, e.g. [2, 1, 3].")
        m = re.search(r"\[[\d,\s]+\]", raw)
    if m is None:
        raise ValueError("reranker sin lista")
    order = json.loads(m.group(0))
    scores = [0.0] * len(docs)
    for rank, idx in enumerate(order):
        if 1 <= idx <= len(docs):
            scores[idx - 1] = float(len(docs) - rank)
    return scores


def rerank(q: str, docs: list[dict], top_n: int = 5, score_fn=None) -> list[dict]:
    score_fn = score_fn or llm_score_fn
    try:
        scores = score_fn(q, docs)
        ranked = sorted(range(len(docs)), key=lambda i: (-scores[i], i))
        return [docs[i] for i in ranked[:top_n]]
    except Exception as e:
        print(f"rerank falló ({e.__class__.__name__}), orden RRF intacto")
        return docs[:top_n]
