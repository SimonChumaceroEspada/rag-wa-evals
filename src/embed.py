import hashlib
import os
import random

DIM = 1536


def _dummy_vector(text: str, dim: int = DIM) -> list[float]:
    """Deterministic dummy embedding (no API key needed)."""
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    rnd = random.Random(seed)
    return [rnd.uniform(-1, 1) for _ in range(dim)]


def embed(texts: list[str]) -> list[list[float]]:
    """Embed texts with OpenAI if key exists, else dummy vectors."""
    key = os.getenv("OPENAI_API_KEY", "")
    if key and not key.startswith("sk-change"):
        from openai import OpenAI

        client = OpenAI()
        model = os.getenv("EMBED_MODEL", "text-embedding-3-small")
        resp = client.embeddings.create(input=texts, model=model)
        return [d.embedding for d in resp.data]
    return [_dummy_vector(t) for t in texts]
