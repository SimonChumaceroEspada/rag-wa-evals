import argparse
import hashlib
import os
import pathlib
import uuid

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from src.chunk import chunk
from src.embed import DIM, embed


def get_client() -> QdrantClient:
    load_dotenv()
    url = os.getenv("QDRANT_URL", "http://localhost:6333")
    return QdrantClient(url=url, timeout=60)


def ensure_collection(client: QdrantClient, name: str):
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
        )


def ingest_lang(lang: str):
    assert lang in ("es", "en"), "lang must be es|en"
    client = get_client()
    col = f"docs_{lang}"
    ensure_collection(client, col)
    data_dir = pathlib.Path(f"data/{lang}")
    files = sorted(data_dir.glob("*.md"))
    if not files:
        print(f"no files in {data_dir}")
        return
    points = []
    for f in files:
        text = f.read_text(encoding="utf-8")
        for c in chunk(text, size=600, overlap=100):
            vec = embed([c])[0]
            pid = str(uuid.UUID(hex=hashlib.md5(c.encode()).hexdigest()))
            points.append(
                PointStruct(
                    id=pid, vector=vec, payload={"text": c, "source": f.name}
                )
            )
    client.upsert(collection_name=col, points=points)
    print(f"{col}: upserted {len(points)} points from {len(files)} files")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True, choices=["es", "en"])
    args = ap.parse_args()
    ingest_lang(args.lang)
