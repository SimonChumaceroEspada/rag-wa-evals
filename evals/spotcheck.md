# Spot-check humano S3-0 (2026-09-27, revisor: asistente; 5 casos del caché)

## Hallazgos
1. **Caché obsoleta (pre-filtro):** varias respuestas guardadas son thinking
   en crudo ("Here's a thinking process..."). El filtro `answer_leaked`
   es posterior al caché → esas respuestas ya no salen a usuarios
   (degradan a extractivo), pero SÍ contaminaron las mediciones.
   Acción: invalidar `.hermes/cache_ask.json` y re-medir.
2. **Recall puntual flojo:** "Growth + P1 → ¿respuesta en cuánto?" no trae
   `SLA.pdf` ni en top-3 (Access_Control, FAQ, DR). Hipótesis: el ES dice
   "Growth" pero el chunk relevante usa otro término de nivel, o el RRF
   premia keyword genérico. Acción: trazar esa Q (ver chunks + scores).
3. **SLA.pdf rankea 3º** en "uptime Enterprise" (detrás de Product_Overview
   y Access_Control): correcto pero mejorable con rerank/tuning.

## Veredicto
faithfulness medida exagera el problema (respuestas viejas sin filtro);
precision 0.4-0.63 sí refleja retrieval real. Orden S3:
re-medir limpio → trazar Q débiles → cobertura/chunks → prompt.
