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
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

QA = pathlib.Path("evals/qa_es.jsonl")
OUT = pathlib.Path("evals/baseline.json")


def qa_path_for(lang: str) -> pathlib.Path:
    if lang not in ("es", "en"):
        raise ValueError(f"lang debe ser es|en, llegó {lang!r}")
    return pathlib.Path(f"evals/qa_{lang}.jsonl")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"(?<=\d)[.,](?=\d)", "", s)  # 99.9% == 99,9% (bilingüe)
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


def live_ask(client, q: str, lang: str = "es") -> dict | None:
    try:
        r = client.get("/ask", params={"q": q, "lang": lang})
        if r.status_code != 200:
            return None
        d = r.json()
        return {"answer": d["answer"], "sources": d["sources"]}
    except Exception as e:
        print(f"live /ask falló ({e.__class__.__name__}), uso fallback offline")
        return None


def offline_ask(q: str, lang: str = "es") -> dict:
    from src.ingest import collect_lang_files, read_doc_text

    docs = []
    for f in collect_lang_files(lang):
        t = read_doc_text(f)
        if t.strip():
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


def judge_faithfulness(q: str, ctx: str, answer: str, base_url: str = "", api_key: str = "", model: str = "", temperature: float = 0.0) -> dict:
    """Juez LLM: ¿cada afirmación de `answer` sale de `ctx`? Solo JSON.
    Defaults: NIM direct (NIM_CHAT_MODEL). Pasar base_url/api_key/model para router/otros.
    """
    import os

    from dotenv import load_dotenv

    load_dotenv()
    from openai import OpenAI

    # Default: juez por el router (gpt-oss-20b, disciplinado y rápido).
    # Fallback: NIM directo. Override explícito vía params.
    if not base_url:
        base_url = os.getenv("FREELLMAPI_BASE_URL", "") or "https://integrate.api.nvidia.com/v1"
    if not api_key:
        api_key = os.getenv("FREELLMAPI_API_KEY", "") or os.getenv("NVIDIA_API_KEY")
    if not model:
        model = "gpt-oss-20b" if "3001" in base_url else os.getenv("NIM_JUDGE_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
    client = OpenAI(base_url=base_url, api_key=api_key, timeout=120)
    prompt = (
        "Grade faithfulness of ANSWER against CONTEXT for QUESTION.\n"
        'Reply with ONLY one JSON object like {"faithfulness": 1, "quote": "...", "reason": "..."}.\n'
        "faithfulness=1 ONLY if every factual claim in ANSWER is supported by CONTEXT, else 0.\n"
        "quote MUST be an exact span copied from CONTEXT that proves your verdict "
        "(for 1: span supporting the answer; for 0: the span it contradicts). "
        "If no such span exists, faithfulness=0.\n"
        'Example: {"faithfulness": 1, "quote": "99.9% de uptime mensual", "reason": "La cifra aparece literal en el contexto."}\n'
        "Copy the quote character-for-character from CONTEXT, never invent it, never write ....\n"
        f"QUESTION: {q}\nCONTEXT:\n{ctx[:3000]}\nANSWER:\n{answer}"
    )
    msgs = [
        {"role": "system", "content": "You are a strict evaluator. You output ONLY one JSON object, never explanations, never thinking."},
        {"role": "user", "content": prompt},
    ]
    def call(messages):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=600,
            temperature=temperature,
        )
        return resp.choices[0].message.content

    def parse(raw):
        import re as _re

        found = _re.findall(r"\{.*?\}", raw, _re.DOTALL)
        for cand in reversed(found):
            try:
                v = json.loads(cand)
                if isinstance(v.get("faithfulness"), int):
                    return v
            except Exception:
                continue
        return None

    raw = None
    v = None
    for attempt in range(3):
        try:
            raw = call(msgs if attempt == 0 else msgs + [{"role": "user", "content": "That was not ONLY JSON. Reply NOW with only the JSON object."}])
            v = parse(raw)
            if v is not None:
                break
        except Exception as e:
            print(f"juez intento {attempt + 1} falló ({e.__class__.__name__}), reintento")
            import time as _t

            _t.sleep(10)
    if v is None:
        return {"verdict": {"faithfulness": None, "reason": "juez no disponible"}, "raw": (raw or "")[:200]}
    # verificación código: la cita debe existir literal en el contexto (mata veredictos cantados)
    q2 = norm(str(v.get("quote", "")))
    if not q2 or q2 not in norm(ctx):
        return {"verdict": {"faithfulness": 0, "reason": "cita del juez no verificada en contexto", "quote": v.get("quote", "")}, "raw": raw[:200]}
    return {"verdict": v, "raw": raw[:200]}


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", action="store_true", help="califica con juez LLM")
    ap.add_argument("--n", type=int, default=0, help="solo primeras N (0=todas)")
    ap.add_argument("--offline", action="store_true", help="fuerza fallback sin Qdrant")
    ap.add_argument("--out", default="", help="archivo salida (default: baseline.json)")
    ap.add_argument("--cache", default=".hermes/cache_ask.json", help="caché respuestas")
    ap.add_argument("--pace", type=float, default=6.0, help="pausa entre llamadas juez")
    ap.add_argument("--fresh", action="store_true", help="ignora caché (re-mide todo)")
    ap.add_argument("--lang", default="es", help="idioma del set (es|en)")
    args = ap.parse_args()
    QA = qa_path_for(args.lang)
    rows = [json.loads(l) for l in QA.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.n:
        rows = rows[: args.n]
    live = qdrant_up() and not args.offline
    client = None
    if live:
        from fastapi.testclient import TestClient

        from api.main import app

        client = TestClient(app)
    else:
        print("modo heuristic-offline para las 30" + (" (--offline)" if args.offline else " (¿Docker apagado?)"))
    live_ok = 0
    f_sum = c_sum = 0.0
    j_sum = j_n = 0
    cache_p = pathlib.Path(args.cache)
    cache = json.loads(cache_p.read_text(encoding="utf-8")) if cache_p.exists() else {}
    import time

    for row in rows:
        res = None
        if live and row["q"] in cache and not args.fresh:
            res = {"answer": cache[row["q"]]["answer"], "sources": cache[row["q"]]["sources"]}
        else:
            res = live_ask(client, row["q"], lang=args.lang) if live else None
        method_live = res is not None
        live_ok += method_live
        if res is None:
            res = offline_ask(row["q"], lang=args.lang)
            ctx = res["_context"]
        else:
            ctx = "\n".join(
                f"[{i + 1}] {s['text']}" for i, s in enumerate(res["sources"])
            )
            if live and row["q"] not in cache:
                cache[row["q"]] = {"answer": res["answer"], "sources": res["sources"]}
                cache_p.write_text(json.dumps(cache), encoding="utf-8")
        hay = norm(res["answer"] + " " + ctx)
        f = 1.0 if norm(row["expected"]) in hay else 0.0
        c = 0.0
        for i, s in enumerate(res["sources"]):
            if s["source"] == row["source"]:
                c = 1.0 / (i + 1)
                break
        f_sum += f
        c_sum += c
        if args.judge:
            jcache_p = pathlib.Path(".hermes/cache_judge.json")
            jcache = json.loads(jcache_p.read_text(encoding="utf-8")) if jcache_p.exists() else {}
            if row["q"] in jcache:
                j = {"verdict": jcache[row["q"]]}
            else:
                j = judge_faithfulness(row["q"], ctx, res["answer"])
                jcache[row["q"]] = j["verdict"]
                jcache_p.write_text(json.dumps(jcache), encoding="utf-8")
                time.sleep(args.pace)
            v = j["verdict"].get("faithfulness")
            if isinstance(v, int):
                j_sum += v
                j_n += 1
            print(f"\nQ: {row['q']}".encode("ascii", "replace").decode())
            print(f"A: {res['answer'][:200]}".encode("ascii", "replace").decode())
            hj = f"heuristico: faithfulness={f} | JUEZ: {j['verdict']}"
            print(hj.encode("ascii", "replace").decode())
    n = len(rows)
    out = {
        "faithfulness": round(f_sum / n, 3) if n else 0.0,
        "context_precision": round(c_sum / n, 3) if n else 0.0,
        "n": n,
        "method": "live" if live_ok == n else "heuristic-offline",
        "live_answers": live_ok,
        "date": datetime.date.today().isoformat(),
    }
    if args.judge and j_n:
        out["judge_faithfulness"] = round(j_sum / j_n, 3)
        out["judge_n"] = j_n
        out["method"] += "+judge"
    dest = pathlib.Path(args.out) if args.out else OUT
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
