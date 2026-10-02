# rag-wa-evals — Bilingual RAG over your own docs, with citations and evals

Ask your documents in **English or Spanish**. One code path (`?lang=en|es`), two corpora,
two Qdrant collections, and every answer cites the sources it used (`[1][2]`).

**Live demo:** <https://rag-wa-evals-web.vercel.app/> — toggle **EN / ES** in the UI.
**API:** `https://rag-wa-evals.onrender.com/ask?q=What%20is%20the%20leave%20policy&lang=en`

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/architecture-dark.svg" />
  <img alt="System architecture: ingest → Qdrant → /ask → answer, gated by evals" src="docs/architecture-light.svg" width="990" />
</picture>

---

## Why this exists

A RAG demo that answers is easy. What is not easy is knowing **why it answers**, **how long
it takes**, and **whether it is actually right**. This project treats those three as the
product: per-stage latency, provider fallback you can observe, and evals that gate every
prompt/model change.

- **Bilingual by construction** — not two apps: one endpoint, `lang` switches corpus + prompt.
- **Verifiable answers** — `[1][2]` inline citations plus the retrieved `sources[]` with scores.
- **Measured, not guessed** — `/ask` returns `timing` for every stage (embed / search / answer).
- **Degrades instead of failing** — three LLM providers in a chain, then an extractive answer.
- **Evaluated** — a 30-question set scores every change; see [Evaluations](#evaluations).

## Latency

Measured against the deployed service on **2026-09-30** (fresh query, no cache):

| stage | before | now | what it does |
|---|---|---|---|
| `embed` | 1.0 s | **1.0 s** | NVIDIA NIM `nemotron-3-embed-1b` |
| `search` | 11.1 s | **1.9 s** | Qdrant dense + BM25 + LLM rerank |
| `answer` | 50.6 s | **0.9 s** | `gemini-3.5-flash-lite` |
| **total** | **62.6 s** | **3.5 s** | 18× faster |

Two real bugs produced those numbers, both found by measuring production rather than
reading code:

1. The chat model `gemini-2.5-flash` had exhausted its free quota (HTTP 429). Every request
   silently fell through to NIM and paid a 25 s timeout. The logs showed
   `ask: gemini falló (RateLimitError)` — the answer was always the fallback.
2. The rerank scorer always failed (`rerank falló (RuntimeError)`) and returned the raw RRF
   order after 10–11 s. You paid for a rerank that never ran, which is why an unrelated
   fixture document ranked first.

The service runs on Render's free tier, which sleeps after 15 minutes idle. It stays
warm by itself: an internal thread (`api/keepalive.py`) pings its own public URL every
10 minutes, and the web UI pings on page load plus every 5 minutes while open. The GitHub
Actions cron (`.github/workflows/keep-alive.yml`) is only a third layer — measured
2026-10-01, GitHub runs scheduled workflows ~5 times a day, not every 10 minutes.

## How it works

```
 data/en/*.md ─┐                                   ┌── docs_en (Qdrant)
 data/es/*.md ─┼─► chunk (600w, overlap 100) ─► embed ┤
 26 PDFs ──────┘        deterministic                └── docs_es (Qdrant)

 GET /ask?q=...&lang=en
      │
      ├─ embed(q)                        ~1.0s
      ├─ Qdrant dense + BM25 → RRF
      │     └─ LLM rerank → top-5        ~1.9s
      └─ LLM chain → answer + [1][2]      ~0.9s
            gemini ─► nim ─► router ─► extractive (no key needed)
```

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/request-sequence-dark.svg" />
  <img alt="Request lifecycle: retrieve → rerank → answer with provider fallback" src="docs/request-sequence-light.svg" width="990" />
</picture>

| file | role |
|---|---|
| `src/chunk.py` | deterministic word splitter with overlap, so no sentence is cut in half |
| `src/embed.py` | `openai` if a real key is set → `nim` → deterministic dummy (offline/tests) |
| `src/ingest.py` | idempotent upserts (`id = hash(text)`): re-running never duplicates |
| `src/hybrid.py` | dense (Qdrant) + BM25 fused with Reciprocal Rank Fusion |
| `src/rerank.py` | LLM listwise rerank of the top-20 → top-5, degrades to RRF order |
| `api/main.py` | FastAPI: retrieval, provider chain, per-stage timing, answer cache |
| `evals/` | ES+EN question sets, heuristic scorer + LLM judge (`run_ragas.py --lang es\|en [--judge]`) |

## Quickstart

```bash
docker compose up -d qdrant                        # or point QDRANT_URL at Qdrant Cloud
python -m venv .venv && .venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env                               # add your keys

python -m src.ingest --lang en
python -m src.ingest --lang es

uvicorn api.main:app --reload --port 8000          # GET /ask?q=...&lang=en
pytest -q                                          # 56 tests
python evals/run_ragas.py                          # writes evals/baseline.json
```

## API

```bash
curl "https://rag-wa-evals.onrender.com/ask?q=What%20is%20the%20leave%20policy&lang=en"
```

```json
{
  "answer": "AcmeTech's leave policy includes 22 days of front-loaded PTO per year with a 5-day carryover cap, 10 separate sick days per year (no doctor's note needed) ... [1]",
  "sources": [
    {"text": "...", "source": "Leave_Policy.pdf", "score": 0.016},
    {"text": "...", "source": "HR_Policy.pdf", "score": 0.016},
    {"text": "...", "source": "Privacy_Policy.pdf", "score": 0.016}
  ],
  "lang": "en",
  "timing": {"embed": 0.94, "search": 1.56, "answer": 1.12, "total": 3.62}
}
```

`lang` defaults to `en`; an unknown value falls back to `en`. Without any provider key the
endpoint still answers through the extractive fallback, so the pipe is testable offline.

## Evaluations

60 questions (30 Spanish + 30 English mirror) over the AcmeTech subset
(`evals/qa_es.jsonl`, `evals/qa_en.jsonl`), answered by the deployed
chain, scored by a deterministic scorer:

| metric | score | n | method | date |
|---|---|---|---|---|
| faithfulness | **0.833** (was 0.733 on Oct 1 morning) | 30 | live answers, heuristic scorer | 2026-10-02 |
| context_precision | **0.818** (was 0.731 on Oct 1 morning) | 30 | live answers, heuristic scorer | 2026-10-02 |
| judge faithfulness | **0.633** (preliminary — verdicts vary run to run, see below) | 30 | live answers, LLM judge (`gpt-oss-20b`, quote verified in code) | 2026-10-01 |
| faithfulness (EN) | **0.967** | 30 | live answers, heuristic scorer (`--lang en`, `qa_en.jsonl`) | 2026-10-02 |
| context_precision (EN) | **0.900** | 30 | live answers, heuristic scorer (`--lang en`, `qa_en.jsonl`) | 2026-10-02 |

The "was" column is the morning baseline. The day moved these numbers: the rerank scorer now
actually runs (it used to fail on every request and hand back the raw RRF order), the answer
now comes from `gemini-3.5-flash-lite` instead of the fallback model the exhausted Gemini
quota was forcing, teaching fixtures left the index, and the prompt bans LaTeX the UI cannot
render. One question in 30 still falls back to NIM when
Gemini hits its rate limit — the chain logs it rather than hiding it.

- **faithfulness** — the expected fact appears in the answer (substring match, 0/1).
- **context_precision** — reciprocal rank of the expected document among retrieved sources.

These are a *plumbing* baseline, not a quality ceiling: the heuristic scorer measures
recall and ranking, not reasoning. The LLM judge (`run_ragas.py --judge`, `gpt-oss-20b`
with its supporting quote verified in code) is stricter — **0.633** — and the gap is
honest signal: answers contain the right fact *plus* embellished extras the context does
not literally support (e.g. a "4h" response time, "5–30%" credits). That gap is the next
thing to close: tighter answer prompt, then re-run.
Honest caveat, measured 2026-10-01: single-call LLM verdicts are unstable — the same
judge flips verdicts on identical inputs across runs (0/6 agreement on a 6-case retry,
even at temperature 0 and via two providers). Until the judge votes (best-of-3) the
heuristic stays the stable headline metric; the judge is directional signal only.

**Golden rule:** no prompt or model change without re-running the evals.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/eval-gate-dark.svg" />
  <img alt="Eval gate: change → tests → evals → merge or blocked" src="docs/eval-gate-light.svg" width="990" />
</picture>

## Corpus: AcmeTech Solutions Inc. (fictional)

AcmeTech is a fictional company from the public dataset
[maruf6890/acmetech-enterprise-rag-dataset](https://github.com/maruf6890/acmetech-enterprise-rag-dataset)
— 26 PDFs across 7 departments, plus a manifest.

> **Permission:** granted verbally by the author on 2026-09-24 (arranged by Simón), with
> attribution and link as given above. The original PDFs are **not committed** (heavy
> binaries): `data/acme/` and `data/acme-es/` are in `.gitignore`.

```bash
git clone --depth 1 https://github.com/maruf6890/acmetech-enterprise-rag-dataset.git /tmp/acme-src
mkdir -p data/acme && cp -r /tmp/acme-src/AcmeTech/* data/acme/
python -m src.ingest --lang en     # 26 PDFs → docs_en
python -m src.ingest --lang es     # 26 hand-translated twins → docs_es
```

## Layout

```
api/      FastAPI service (+ legacy static UI)
src/      chunk · embed · ingest · hybrid · rerank
data/     en/ es/ corpora (PDFs fetched, not committed)
evals/    question sets, scorer, baselines
tests/    pytest suite (56)
web/      Next.js frontend on Vercel
```

## Roadmap

**S1 (this repo):** bilingual ingest, `/ask` with citations, per-stage timing, ES+EN eval baselines, self-keep-alive.
**Next:** WhatsApp + voice, DeepEval + Langfuse.

---

## Español

RAG bilingüe sobre tus documentos: preguntas en `GET /ask?q=...&lang=en|es` y respuestas que
**citan** tus fuentes (`[1][2]` + `sources[]`). Una sola ruta de código, dos corpus
(`data/en`, `data/es`), dos colecciones Qdrant (`docs_en`, `docs_es`). El idioma por defecto
es inglés; sin claves de proveedor sigue respondiendo con el fallback extractivo.

Medido el 2026-10-01: **3.5 s** por consulta (antes 62.6 s). Las métricas de la tabla son un
baseline de *plomería* (recuerdo y ranking, no razonamiento); el juez LLM (`--judge`) ya
corre y es más estricto (**0.633**): detecta adornos que el contexto no respalda. Sin Docker/Qdrant, `/ask` y los tests que lo usan fallan por conexión, no por
código: arranca con `docker compose up -d qdrant`.
