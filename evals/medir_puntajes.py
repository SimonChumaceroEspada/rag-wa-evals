"""Compara los puntajes de relevancia: preguntas del corpus vs fuera del corpus.

Sirve para elegir un umbral determinista: si nada es relevante, no llamamos al LLM
y respondemos 'no tengo esa información' (evita que el modelo de respaldo alucine).
"""
import sys

sys.path.insert(0, ".")
from api.main import embed, get_client
from src.hybrid import hybrid_search
from src.rerank import rerank

DENTRO = [
    "¿Cuántos días de vacaciones al año hay?",
    "What uptime does AcmeTech guarantee Enterprise?",
    "What is the P1 response time for Enterprise?",
]
FUERA = [
    "What is the capital of France?",
    "who won the world cup in 2022?",
    "¿cómo cocino una pizza?",
]

client = get_client()
print(f"{'tipo':7s} {'top1':>7s} {'top2':>7s} {'top5 minima':>12s}  pregunta")
for tipo, grupo in (("DENTRO", DENTRO), ("FUERA", FUERA)):
    for q in grupo:
        lang = "es" if any(c in q for c in "¿áéíóúñ") else "en"
        qvec = embed([q])[0]
        cands = hybrid_search(client, lang, qvec, q, k_dense=10, k_bm25=10, k_final=20)
        src = rerank(q, cands, top_n=5)
        sc = [round(float(s.get("score", 0)), 4) for s in src]
        while len(sc) < 5:
            sc.append(0.0)
        t1, t2, t5 = sc[0], sc[1], min(sc)
        print(f"{tipo:7s} {t1:7.3f} {t2:7.3f} {t5:12.3f}  {q[:52]}")
