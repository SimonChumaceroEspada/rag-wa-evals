"""Bench de jueces sobre casos congelados (sin llamadas /ask nuevas).

Compara en las mismas 5 Q (respuesta+contexto del caché):
 A) llama-3.1-8b-instruct vía router FreeLLMAPI (Groq)
 B) nemotron-3.5-lightning directo NIM (juez actual)
Métrica: veredictos 1/0 + % citas verificadas en código.
"""

import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()

from evals.run_ragas import judge_faithfulness, norm  # noqa: E402

QA = [json.loads(l) for l in open("evals/qa_es.jsonl", encoding="utf-8") if l.strip()][:5]
CACHE = json.load(open(".hermes/cache_ask.json", encoding="utf-8"))
ROUTER = os.getenv("FREELLMAPI_BASE_URL", "http://localhost:3001/v1")
RKEY = os.getenv("FREELLMAPI_API_KEY", "")

JUDGES = [
    ("router-gptoss20b", ROUTER, RKEY, "gpt-oss-20b"),
    ("nim-lightning", "", "", "nvidia/nemotron-3.5-lightning-30b-a3b"),
]

for name, url, key, model in JUDGES:
    ok = ver = 0
    print(f"\n=== {name} ({model}) ===")
    for row in QA:
        c = CACHE.get(row["q"])
        if not c:
            print("  sin caché:", row["q"][:50])
            continue
        ctx = "\n".join(f"[{i + 1}] {s['text']}" for i, s in enumerate(c["sources"]))
        try:
            j = judge_faithfulness(row["q"], ctx, c["answer"], base_url=url, api_key=key, model=model)
        except Exception as e:
            print(f"  Q {row['q'][:40]!r} -> ERROR {e.__class__.__name__}")
            continue
        v = j["verdict"]
        q2 = norm(str(v.get("quote", "")))
        verified = bool(q2) and q2 in norm(ctx)
        ver += verified
        ok += 1
        print(f"  f={v.get('faithfulness')} verif={verified} | {str(v.get('reason', ''))[:70]}")
    print(f">> {name}: {ok} veredictos, citas verificadas {ver}/{ok}")
