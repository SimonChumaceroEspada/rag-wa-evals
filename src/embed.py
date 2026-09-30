import hashlib
import os
import random

OPENAI_DIM = 1536
# nvidia/nemotron-3-embed-1b (verificado servible 2026-09-25).
NIM_EMBED_MODEL = os.getenv("NIM_EMBED_MODEL", "nvidia/nemotron-3-embed-1b")
NIM_DIM = 2048
DUMMY_DIM = 1536
NIM_URL = "https://integrate.api.nvidia.com/v1"


def provider() -> str:
    """openai (key) > nim (key) > dummy (offline). Evaluado tarde (post-dotenv)."""
    ok = os.getenv("OPENAI_API_KEY", "")
    if ok and not ok.startswith("sk-change"):
        return "openai"
    if os.getenv("NVIDIA_API_KEY", ""):
        return "nim"
    return "dummy"


def embed_dim() -> int:
    return {"openai": OPENAI_DIM, "nim": NIM_DIM, "dummy": DUMMY_DIM}[provider()]


def _dummy_vector(text: str, dim: int = DUMMY_DIM) -> list[float]:
    """Deterministic dummy embedding (no API key needed)."""
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    rnd = random.Random(seed)
    return [rnd.uniform(-1, 1) for _ in range(dim)]


def embed(texts: list[str]) -> list[list[float]]:
    """Embed texts. Acepta lista (batching: 1 request por lote, no por chunk)."""
    from openai import OpenAI

    # timeout corto + 1 reintento: sin acotar, el cliente espera 120s x3
    tw = float(os.getenv("EMBED_TIMEOUT", "30"))
    p = provider()
    if p == "openai":
        client = OpenAI(timeout=tw, max_retries=1)
        model = os.getenv("EMBED_MODEL", "text-embedding-3-small")
        resp = client.embeddings.create(input=texts, model=model)
        return [d.embedding for d in resp.data]
    if p == "nim":
        client = OpenAI(base_url=NIM_URL, api_key=os.getenv("NVIDIA_API_KEY"), timeout=tw, max_retries=1)
        resp = client.embeddings.create(input=texts, model=NIM_EMBED_MODEL)
        return [d.embedding for d in resp.data]
    return [_dummy_vector(t) for t in texts]
