# rag-wa-evals — Bilingual RAG (ES/EN) with citations + evals

Ask your own docs in Spanish or English. One code path, `?lang=es|en`, two corpora, answers with citations.

```bash
docker compose up -d qdrant          # vector DB → http://localhost:6333/dashboard
python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt
python -m src.ingest --lang es && python -m src.ingest --lang en
uvicorn api.main:app --port 8000    # GET /ask?q=gatos&lang=es
python evals/run_ragas.py           # writes evals/baseline.json
```

## How it works

```
data/es|en/*.md --> chunk(600w, overlap 100) --> embed() --> Qdrant docs_es|docs_en
                                                                            |
GET /ask?q=...&lang=es --> embed(q) --> top-5 cosine --> prompt [1][2] --> {answer, sources[]}
```

- `src/chunk.py` — deterministic word splitter with overlap (no idea gets cut in half).
- `src/embed.py` — OpenAI `text-embedding-3-small` when `OPENAI_API_KEY` is set, deterministic dummy vectors offline.
- `src/ingest.py` — idempotent upserts (`id = hash(text)`): re-running never duplicates.
- `api/main.py` — retrieval (top-5) + LLM answer with `[1][2]` citations; extractive fallback without a key.
- `evals/` — 30 ES Q&A (`qa_es.jsonl`) + scorer (`run_ragas.py`). Golden rule: **no prompt/model change without re-running evals.**

## API

```bash
curl "http://localhost:8000/ask?q=gatos&lang=es"
# {"answer": "Basado en [1]: ... [1]", "sources": [{"text": "...", "source": "gatos.md", "score": 0.9}], "lang": "es"}
```

## Metrics (S1 baseline)

| metric | score | n | method | date |
|---|---|---|---|---|
| faithfulness | 1.0 | 30 | heuristic-offline | 2026-09-23 |
| context_precision | 0.983 | 30 | heuristic-offline | 2026-09-23 |

> `heuristic-offline` = extractive fallback + keyword retrieval (no LLM judge yet). Scores are inflated by design — they prove the pipe works, not quality. Re-run with a real LLM (NVIDIA NIM planned) for the true baseline before changing prompts.

## Layout

`src/` (chunk, embed, ingest) · `api/` (FastAPI) · `data/es|en/` (corpora) · `evals/` (Q&A + scorer) · `tests/` (`pytest -q`)

## Roadmap

S1 (here): ingest + `/ask` + baseline. Next: WhatsApp + voice, DeepEval + Langfuse.

## Español

RAG bilingüe sobre tus documentos: preguntas en `GET /ask?q=...&lang=es|en` y responde **citando** tus docs (`[1][2]` + `sources[]`). Una sola ruta de código, dos corpus (`data/es`, `data/en`), dos colecciones Qdrant (`docs_es`, `docs_en`). Los comandos son los mismos de arriba. Las métricas de la tabla son el baseline S1 (heurístico offline: alto por copiar, no por razonar — el baseline real con LLM viene en el siguiente paso). Sin Docker corriendo, `/ask` y los tests que usan Qdrant fallan por conexión, no por código: arranca con `docker compose up -d qdrant`.
