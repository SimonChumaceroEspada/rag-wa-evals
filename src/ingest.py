import argparse
import hashlib
import os
import pathlib
import uuid

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.chunk import chunk
from src.embed import embed, embed_dim, provider


def get_client() -> QdrantClient:
    load_dotenv()
    local_path = os.getenv("QDRANT_LOCAL_PATH", "")
    if local_path:
        # Modo local sin Docker (CI / verificación offline).
        return QdrantClient(path=local_path)
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=url, timeout=60)


def ensure_collection(client: QdrantClient, name: str):
    dim = embed_dim()
    if client.collection_exists(name):
        cur = client.get_collection(name).config.params.vectors.size
        if cur != dim:
            print(f"{name}: dim {cur} -> {dim} (cambio de proveedor), recreo colección")
            client.delete_collection(name)
        else:
            return
    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )


def read_pdf_text(path: pathlib.Path) -> str:
    """Extract text from a PDF: pypdf first, pdfplumber fallback.

    Returns "" (warns) if both fail so one bad file never kills ingest.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        if text.strip():
            return text
    except Exception as e:
        print(f"pypdf falló en {path.name} ({e.__class__.__name__}), pruebo pdfplumber")
    try:
        import pdfplumber

        with pdfplumber.open(str(path)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        if text.strip():
            return text
    except Exception as e:
        print(f"pdfplumber falló en {path.name} ({e.__class__.__name__})")
    print(f"WARN: sin texto extraíble en {path}")
    return ""


def read_doc_text(path: pathlib.Path) -> str:
    if path.suffix.lower() == ".pdf":
        return read_pdf_text(path)
    return path.read_text(encoding="utf-8")


LANG_DIRS = {
    # EN: demo legacy + los 26 PDFs originales del corpus Acme.
    "en": ["data/en", "data/acme"],
    # ES: demo legacy + los 26 PDFs Acme traducidos (gemelos de los EN).
    "es": ["data/es", "data/acme-es"],
}


def collect_files(data_dir: pathlib.Path) -> list[pathlib.Path]:
    """All ingestible docs under data_dir (recursive: keeps Acme Dept/ layout)."""
    files = [f for f in sorted(data_dir.rglob("*")) if f.suffix.lower() in (".md", ".pdf") and f.is_file()]
    return files


def collect_lang_files(lang: str) -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for d in LANG_DIRS[lang]:
        p = pathlib.Path(d)
        if p.exists():
            files.extend(collect_files(p))
    return sorted(files)


def ingest_lang(lang: str):
    assert lang in ("es", "en"), "lang must be es|en"
    client = get_client()
    col = f"docs_{lang}"
    ensure_collection(client, col)
    data_dir = pathlib.Path(f"data/{lang}")
    files = collect_lang_files(lang)
    if not files:
        print(f"no files for lang={lang} (dirs: {LANG_DIRS[lang]})")
        return
    n_files = len(files)
    items = []  # (pid, text, source)
    for f in files:
        text = read_doc_text(f)
        if not text.strip():
            continue
        for c in chunk(text, size=600, overlap=100):
            pid = str(uuid.UUID(hex=hashlib.md5(c.encode()).hexdigest()))
            items.append((pid, c, f.name))
    print(f"{col}: {len(items)} chunks de {n_files} files (provider={provider()})")
    for i in range(0, len(items), 32):  # batching: 1 request por lote
        batch = items[i : i + 32]
        vecs = embed([c for _, c, _ in batch])
        client.upsert(
            collection_name=col,
            points=[
                PointStruct(id=pid, vector=v, payload={"text": c, "source": s})
                for (pid, c, s), v in zip(batch, vecs)
            ],
        )
    print(f"{col}: upserted {len(items)} points")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=["es", "en"])
    args = ap.parse_args()
    ingest_lang(args.lang)
