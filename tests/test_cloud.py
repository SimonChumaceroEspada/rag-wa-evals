import os


def test_get_client_accepts_cloud_key(monkeypatch):
    monkeypatch.setenv("QDRANT_URL", "https://xxx.cloud.qdrant.io:6333")
    monkeypatch.setenv("QDRANT_API_KEY", "fake")
    from qdrant_client import QdrantClient

    from src.ingest import get_client

    assert isinstance(get_client(), QdrantClient)
    assert os.getenv("QDRANT_API_KEY") == "fake"
