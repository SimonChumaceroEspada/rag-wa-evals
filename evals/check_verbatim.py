"""Verifica que cada `expected` de un set de preguntas aparezca LITERALMENTE en su PDF fuente.

Uso:  python evals/check_verbatim.py <qa.jsonl> <pdf_texts.json> [--desde N]
- qa.jsonl:      lineas {"q","expected","source"}
- pdf_texts.json: {"Nombre_Archivo.pdf": "texto completo...", ...}
Sale con codigo != 0 si alguna cita no aparece.
"""
import json
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    """Normaliza para comparar: minusculas, espacios colapsados, sin espacios finos."""
    s = s.replace("\u00a0", " ").replace("\u2009", " ").replace("\u202f", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def main() -> int:
    qa_path, texts_path = sys.argv[1], sys.argv[2]
    desde = 0
    if "--desde" in sys.argv:
        desde = int(sys.argv[sys.argv.index("--desde") + 1])

    qa = [json.loads(l) for l in Path(qa_path).read_text(encoding="utf-8").splitlines() if l.strip()]
    crudos = json.loads(Path(texts_path).read_text(encoding="utf-8"))
    # Las claves pueden venir como "Carpeta\Archivo.pdf" -> indexamos tambien por nombre base.
    textos: dict[str, str] = {}
    ambiguos = set()
    for k, v in crudos.items():
        base = re.split(r"[\\/]", k)[-1]
        if base in textos and textos[base] != norm(v):
            ambiguos.add(base)
        textos[base] = norm(v)
    if ambiguos:
        print(f"AVISO: nombre de archivo repetido en carpetas distintas: {sorted(ambiguos)}")

    nuevas = qa[desde:]
    ok = fallan = 0
    faltantes = []
    por_archivo: dict[str, int] = {}

    for i, item in enumerate(nuevas, start=desde + 1):
        src = item.get("source", "")
        exp = norm(item.get("expected", ""))
        por_archivo[src] = por_archivo.get(src, 0) + 1
        texto = textos.get(src)
        if texto is None:
            print(f"linea {i}: FUENTE DESCONOCIDA -> {src}")
            fallan += 1
            faltantes.append((i, src, item.get("expected", ""), "no existe ese PDF"))
            continue
        if exp and exp in texto:
            ok += 1
        else:
            fallan += 1
            faltantes.append((i, src, item.get("expected", ""), "cita no aparece en el PDF"))

    print(f"\nrevisadas: {len(nuevas)}   cita literal OK: {ok}   fallan: {fallan}")
    if faltantes:
        print("\n--- las que fallan ---")
        for i, src, exp, motivo in faltantes[:25]:
            print(f"linea {i} [{src}] {motivo}: {exp[:90]!r}")
    print("\n--- reparto por archivo (maximo permitido: 4) ---")
    for src, n in sorted(por_archivo.items(), key=lambda x: -x[1]):
        marca = "  <-- PASA DE 4" if n > 4 else ""
        print(f"{n:3d}  {src}{marca}")
    return 0 if fallan == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
