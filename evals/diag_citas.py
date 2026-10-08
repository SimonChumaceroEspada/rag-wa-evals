"""Para cada cita que falla, muestra que dice el PDF de verdad alrededor de sus anclas.

Uso: python evals/diag_citas.py <qa.jsonl> <pdf_texts.json> <linea> [<linea> ...]
Las anclas son los numeros y las palabras largas de la cita (lo mas distintivo).
"""
import json
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    s = s.replace("\u00a0", " ").replace("\u2009", " ").replace("\u202f", " ")
    return re.sub(r"\s+", " ", s).strip().lower()


def anclas(cita: str) -> list[str]:
    piezas = re.findall(r"[\w$%/.,]{3,}", cita, flags=re.UNICODE)
    piezas = [p for p in piezas if any(c.isdigit() for c in p) or len(p) >= 7]
    piezas.sort(key=len, reverse=True)
    return piezas[:6]


def main() -> int:
    qa = [json.loads(l) for l in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines() if l.strip()]
    crudos = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    textos = {re.split(r"[\\/]", k)[-1]: v for k, v in crudos.items()}

    for num in (int(x) for x in sys.argv[3:]):
        item = qa[num - 1]
        src = item.get("source", "")
        cita = item.get("expected", "")
        texto = textos.get(src, "")
        print("=" * 90)
        print(f"linea {num}  [{src}]")
        print(f"  pregunta: {item.get('q', '')}")
        print(f"  cita del agente: {cita!r}")
        encontradas = [a for a in anclas(cita) if norm(a) in norm(texto)]
        print(f"  anclas que SI estan en el PDF: {encontradas or 'NINGUNA'}")
        for a in encontradas[:2]:
            t = norm(texto)
            i = t.find(norm(a))
            print(f"    ...{t[max(0, i - 120):i + 160]}...")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
