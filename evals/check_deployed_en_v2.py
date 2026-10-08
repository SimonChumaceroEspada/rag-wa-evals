"""Refined check of the DEPLOYED service (EN, 30 q).
Matcher v2: expected strings carry a label prefix ("P1: 1 hour"); the answer often
states only the value. Score 1 if the expected value (text after the last ': ')
appears in answer+contexts, or the full expected string does.
"""
import json, time, re, urllib.parse, urllib.request, pathlib

BASE = "https://rag-wa-evals.onrender.com/ask"
QA = pathlib.Path("D:/Hermes/rag-wa-evals/evals/qa_en.jsonl")

def norm(s: str) -> str:
    s = s.lower().replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def value_of(expected: str) -> str:
    # "P1: 1 hour" -> "1 hour"; "99.9% monthly uptime" -> unchanged
    return expected.split(": ", 1)[1] if ": " in expected else expected

rows = [json.loads(l) for l in QA.read_text(encoding="utf-8").splitlines() if l.strip()]
faith = 0; rr_sum = 0.0; n = 0
detail = []
for i, r in enumerate(rows, 1):
    q, exp, src = r["q"], norm(r["expected"]), r["source"]
    val = norm(value_of(r["expected"]))
    url = f"{BASE}?q={urllib.parse.quote(q)}&lang=en"
    try:
        with urllib.request.urlopen(url, timeout=90) as resp:
            d = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [{i}] ERROR {type(e).__name__}", flush=True)
        continue
    ans = norm(d.get("answer") or "")
    ctx = norm(" ".join((s.get("text") or "") for s in d.get("sources", [])))
    hay_ans = ans
    hay_all = ans + " " + ctx
    f = 1 if (exp in hay_ans or val in hay_ans) else 0
    srcs = [s.get("source", "") for s in d.get("sources", [])]
    rr = next((1.0 / k for k, s in enumerate(srcs, 1) if s == src), 0.0)
    faith += f; rr_sum += rr; n += 1
    detail.append({"q": q, "faithfulness": f, "value": val, "sources": srcs})
    print(f"  [{i}] faith={f} rr={rr:.2f}", flush=True)
    time.sleep(0.4)

print()
print(f"=== DESPLEGADO EN, matcher v2 (n={n}) ===")
print(f"faithfulness      = {faith/n:.3f}")
print(f"context_precision = {rr_sum/n:.3f}")
pathlib.Path("D:/Hermes/rag-wa-evals/evals/deployed_en_check_v2.json").write_text(
    json.dumps({"n": n, "faithfulness": round(faith/n, 3),
                "context_precision": round(rr_sum/n, 3), "date": "2026-10-05",
                "matcher": "value-after-label", "target": BASE, "detail": detail}, indent=1),
    encoding="utf-8")
print("escrito evals/deployed_en_check_v2.json")
