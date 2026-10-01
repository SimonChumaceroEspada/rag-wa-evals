"""Bench de jueces LLM sobre casos congelados (sin /ask nuevas).

Compara candidatos en las mismas 6 Q (respuesta+contexto del caché de hoy):
veredictos 1/0, % citas verificadas en código, latencia, acuerdo con el juez actual.
Uso: .venv/Scripts/python.exe evals/bench_judges.py
"""

import json
import os
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from evals.run_ragas import judge_faithfulness, norm  # noqa: E402

QA = [json.loads(l) for l in open("evals/qa_es.jsonl", encoding="utf-8") if l.strip()][:6]
CACHE = json.load(open(".hermes/cache_ask.json", encoding="utf-8"))
ROUTER = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")
RKEY = os.getenv("FREELLMAPI_API_KEY", "")

CANDIDATES = [
    ("actual/gpt-oss-20b", ROUTER, RKEY, "gpt-oss-20b"),
    ("llama-3.3-70b-instruct", ROUTER, RKEY, "llama-3.3-70b-instruct"),
    ("qwen2.5-72b-instruct", ROUTER, RKEY, "qwen2.5-72b-instruct"),
    ("gemini-2.5-flash", ROUTER, RKEY, "gemini-2.5-flash"),
]

results = {}
for name, url, key, model in CANDIDATES:
    ok = ver = ones = 0
    lat = []
    print(f"\n=== {name} ===")
    for row in QA:
        c = CACHE.get(row["q"])
        if not c:
            print("  sin caché:", row["q"][:50])
            continue
        ctx = "\n".join(f"[{i + 1}] {s['text']}" for i, s in enumerate(c["sources"]))
        t0 = time.time()
        try:
            j = judge_faithfulness(row["q"], ctx, c["answer"], base_url=url, api_key=key, model=model)
        except Exception as e:
            print(f"  Q {row['q'][:40]!r} -> ERROR {e.__class__.__name__}")
            continue
        lat.append(time.time() - t0)
        v = j["verdict"]
        q2 = norm(str(v.get("quote", "")))
        verified = bool(q2) and q2 in norm(ctx)
        ver += verified
        ok += 1
        ones += 1 if v.get("faithfulness") == 1 else 0
        print(f"  f={v.get('faithfulness')} verif={verified} {lat[-1]:.0f}s | {str(v.get('reason', ''))[:60]}")
        time.sleep(4)
    results[name] = {"veredictos": ok, "unos": ones, "citas_ok": f"{ver}/{ok}",
                     "lat_media": round(sum(lat) / len(lat), 1) if lat else None}
    print(f">> {name}: {results[name]}")

print("\n=== RESUMEN ===")
print(json.dumps(results, indent=2))
