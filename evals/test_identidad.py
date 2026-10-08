"""Prueba el arreglo: identidad, fuera de corpus, y una pregunta real del corpus."""
import sys

sys.path.insert(0, ".")
from fastapi.testclient import TestClient

from api.main import app

CASOS = [
    ("who are you and what you do? how can you help me?", "en", "IDENTIDAD"),
    ("¿quién sos y qué podés hacer?", "es", "IDENTIDAD"),
    ("What is the capital of France?", "en", "FUERA DE CORPUS"),
    ("¿Cuántos días de vacaciones al año hay?", "es", "CORPUS (debe citar)"),
    ("What is the P1 response time for Enterprise?", "en", "CORPUS (debe citar)"),
]

with TestClient(app) as c:
    for q, lang, tipo in CASOS:
        r = c.get("/ask", params={"q": q, "lang": lang})
        d = r.json()
        ans = (d.get("answer") or "").strip()
        fuentes = [s.get("source") for s in (d.get("sources") or [])][:3]
        citas = ans.count("[")
        print("=" * 78)
        print(f"[{tipo}]  ({lang})  {q}")
        print(f"  respuesta: {ans[:240]}")
        print(f"  citas en la respuesta: {citas} | fuentes: {fuentes}")
