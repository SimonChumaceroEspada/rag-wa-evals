# S1 — Examen final (2026-09-23)

Nota: **4.0 / 5 — APROBADO** (mínimo 4/5)

| # | Task | Puntaje | Comentario |
|---|---|---|---|
| P1 | T1 Qdrant/payload | 1.0 | Correcto: el texto se guarda para extraer el contexto y responder. Matiz: el vector solo sirve para buscar (números ilegibles, no se puede reconstruir el párrafo desde él). |
| P2 | T2 overlap | 1.0 | Correcto: con `overlap=0` la idea se corta a la mitad y parte del contexto no llega a la respuesta. |
| P3 | T3 idempotencia | 0.5 | Idea correcta (la info ya está) pero faltó el mecanismo: `id = UUID(MD5(texto))` → el segundo ingest genera el MISMO id y `upsert` sobrescribe en vez de duplicar. Sin ese id determinista, la DB sí duplicaría. |
| P4 | T4 alucinación/citas | 1.0 | Correcto: alucinación; las citas anclan la respuesta a fuentes verificables (y `faithfulness` mide justo eso: apoyo en el contexto). |
| P5 | Integradora /ask | 0.5 | El esqueleto está (vector → búsqueda → respuesta con citas), pero faltaron 3 piezas: `lang=es` enruta a `docs_es`, se traen top-5 por coseno (no 1), y esos textos se pegan al prompt como `[1][2]` para anclar al LLM. |

Repasar: mecanismo de `id=hash` (P3) y traza completa con idioma + top-5 + prompt (P5).
Siguiente: baseline real con LLM (NIM) y re-ejecutar evals antes de cualquier cambio de prompt.
