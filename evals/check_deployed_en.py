"""Verify the DEPLOYED service's honesty numbers (EN set, 30 questions).
Mirrors evals/run_ragas.py scoring: faithfulness = expected substring in answer+contexts;
context_precision = reciprocal rank of expected source among returned sources.
"""
import json, time, urllib.parse, urllib.request, pathlib, sys

BASE = "https://rag-wa-evals.onrender.com/ask"
QA = pathlib.Path("D:/Hermes/rag-wa-evals/evals/qa_en.jsonl")

rows = [json.loads(l) for l in QA.read_text(encoding="utf-8").splitlines() if l.strip()]
print(f"preguntas: {len(rows)}", flush=True)

faith_hits = 0
rr_sum = 0.0
scored = 0
detail = []
for i, r in enumerate(rows, 1):
    q = r["q"]; exp = r["expected"].lower(); src = r["source"]
    url = f"{BASE}?q={urllib.parse.quote(q)}&lang=en"
    try:
        with urllib.request.urlopen(url, timeout=90) as resp:
            d = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [{i}] ERROR {type(e).__name__}: {e}", flush=True)
        continue
    ans = (d.get("answer") or "")
    ctxs = " ".join((s.get("text") or "") for s in d.get("sources", []))
    hay = (ans + " " + ctxs).lower()
    f = 1 if exp in hay else 0
    srcs = [s.get("source", "") for s in d.get("sources", [])]
    rr = 0.0
    for rank, s in enumerate(srcs, 1):
        if s == src:
            rr = 1.0 / rank
            break
    faith_hits += f
    rr_sum += rr
    scored += 1
    detail.append({"q": q, "faithfulness": f, "rr": rr, "sources": srcs, "expected_src": src})
    print(f"  [{i}] faith={f} rr={rr:.2f} srcs={srcs[:3]}", flush=True)
    time.sleep(0.5)

print()
print(f"=== DESPLEGADO (EN, n={scored}) ===")
print(f"faithfulness     = {faith_hits/scored:.3f}")
print(f"context_precision= {rr_sum/scored:.3f}")
pathlib.Path("D:/Hermes/rag-wa-evals/evals/deployed_en_check.json").write_text(
    json.dumps({"n": scored, "faithfulness": faith_hits/scored,
                "context_precision": rr_sum/scored, "date": "2026-10-05",
                "target": BASE, "detail": detail}, indent=1), encoding="utf-8")
print("escrito evals/deployed_en_check.json")
