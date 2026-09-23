"""Baseline S1: heurístico offline (sin LLM-as-judge).

Intenta /ask en vivo (TestClient -> Qdrant). Si Qdrant está caído
(Docker apagado), cae a retrieval por keywords sobre data/es/*.md
con respuesta extractiva. Mide:
- faithfulness: ¿el `expected` aparece en answer+contextos? (1/0)
- context_precision: reciprocal rank del `source` esperado en sources.
Escribe evals/baseline.json. Con key NIM/OpenAI se re-ejecuta con
LLM-as-judge real (Ragas) y se compara contra este baseline.
"""

import datetime
import json
import pathlib
import re
import unicodedata

QA = pathlib.Path("evals/qa_es.jsonl")
OUT = pathlib.Path("evals/baseline.json")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


def tokens(s: str) -> set:
    return set(norm(s).split())


def qdrant_up() -> bool:
    import urllib.request

    try:
        with urllib.request.urlopen("http://localhost:6333/collections", timeout=2):
            return True
    except Exception:
        return False


def live_ask(client, q: str) -> dict | None:
    try:
        r = client.get("/ask", params={"q": q, "lang": "es"})
        if r.status_code != 200:
            return None
        d = r.json()
        return {"answer": d["answer"], "sources": d["sources"]}
    except Exception as e:
        print(f"live /ask falló ({e.__class__.__name__}), uso fallback offline")
        return None


def offline_ask(q: str) -> dict:
    docs = []
    for f in sorted(pathlib.Path("data/es").glob("*.md")):
        t = f.read_text(encoding="utf-8")
        docs.append({"text": t, "source": f.name})
    qt = tokens(q)
    ranked = sorted(
        docs, key=lambda d: len(qt & tokens(d["text"])), reverse=True
    )[:2]
    ctx = "\n".join(f"[{i + 1}] {d['text']}" for i, d in enumerate(ranked))
    first = f"[1] {ranked[0]['text']}" if ranked else ""
    return {
        "answer": f"Basado en [1]: {first} [1]",
        "sources": [
            {"text": d["text"], "source": d["source"], "score": 1.0 - i * 0.1}
            for i, d in enumerate(ranked)
        ],
        "_context": ctx,
    }


def main():
    rows = [json.loads(l) for l in QA.read_text(encoding="utf-8").splitlines() if l.strip()]
    live = qdrant_up()
    client = None
    if live:
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)
    else:
        print("Qdrant caído (¿Docker apagado?), modo heuristic-offline para las 30")
    live_ok = 0
    f_sum = c_sum = 0.0
    for row in rows:
        res = live_ask(client, row["q"]) if live else None
        method_live = res is not None
        live_ok += method_live
        if res is None:
            res = offline_ask(row["q"])
            ctx = res["_context"]
        else:
            ctx = "\n".join(
                f"[{i + 1}] {s['text']}" for i, s in enumerate(res["sources"])
            )
        hay = norm(res["answer"] + " " + ctx)
        f = 1.0 if norm(row["expected"]) in hay else 0.0
        c = 0.0
        for i, s in enumerate(res["sources"]):
            if s["source"] == row["source"]:
                c = 1.0 / (i + 1)
                break
        f_sum += f
        c_sum += c
    n = len(rows)
    out = {
        "faithfulness": round(f_sum / n, 3) if n else 0.0,
        "context_precision": round(c_sum / n, 3) if n else 0.0,
        "n": n,
        "method": "live" if live_ok == n else "heuristic-offline",
        "live_answers": live_ok,
        "date": datetime.date.today().isoformat(),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
