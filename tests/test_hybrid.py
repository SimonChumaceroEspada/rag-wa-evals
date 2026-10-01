from src.hybrid import build_fixture_index, rrf_fuse, search_bm25


def test_bm25_exact_token_wins():
    docs = [
        "el endpoint /refunds acepta POST con id",
        "guia de devoluciones y reembolsos general",
        "politica de vacaciones de la empresa",
    ]
    idx = build_fixture_index(docs)
    top = search_bm25(idx, "/refunds", k=3)
    assert top[0][0] == 0  # id del doc con el token exacto


def test_rrf_fuse_unites_and_orders():
    fused = rrf_fuse([("a", 0.9)], [("b", 12.0), ("a", 3.0)], k=60)
    assert [i for i, _ in fused] == ["a", "b"]  # a suma ambos rankings


class _Point:
    def __init__(self, pid: str, text: str, source: str):
        self.id = pid
        self.payload = {"text": text, "source": source}


class _StubClient:
    """Qdrant mínimo: lo que usa get_index (get_collection + scroll)."""

    def __init__(self, points):
        self._pts = points

    def get_collection(self, name):
        from types import SimpleNamespace

        return SimpleNamespace(points_count=len(self._pts))

    def scroll(self, collection_name, limit, offset, with_payload=None, with_vectors=False):
        return list(self._pts), None


def _isolated_cache(tmp_path, monkeypatch):
    import src.hybrid as h

    monkeypatch.setattr(h, "_INDEX_CACHE", {})
    monkeypatch.setattr(
        h, "_cache_paths", lambda lang: (tmp_path / f"{lang}.pkl", tmp_path / f"{lang}.meta.json")
    )


def test_index_builds_from_qdrant_payloads(tmp_path, monkeypatch):
    """Render no despliega los PDFs: el BM25 debe salir de Qdrant, no del disco."""
    from src.hybrid import get_index, search_bm25

    _isolated_cache(tmp_path, monkeypatch)
    pts = [
        _Point("00000000-0000-0000-0000-000000000001", "reembolsos vía /refunds en 3 días", "Refund.pdf"),
        _Point("00000000-0000-0000-0000-000000000002", "política de vacaciones 22 días", "Leave.pdf"),
        # 3er doc: con N=2 el idf de BM25 da log(1.5)-log(1.5)=0 y todo puntúa 0
        _Point("00000000-0000-0000-0000-000000000003", "guía de onboarding de nuevos ingresos", "Onboarding.pdf"),
    ]
    idx = get_index("en", _StubClient(pts))
    assert idx["ids"] == [p.id for p in pts], "los ids deben ser los de Qdrant para poder fusionarlos"
    assert idx["sources"] == ["Refund.pdf", "Leave.pdf", "Onboarding.pdf"]
    assert search_bm25(idx, "/refunds", k=3)[0][0] == pts[0].id


def test_empty_collection_does_not_raise(tmp_path, monkeypatch):
    """Sin chunks no hay que lanzar: el fallback denso era la consecuencia."""
    from src.hybrid import get_index, search_bm25

    _isolated_cache(tmp_path, monkeypatch)
    idx = get_index("en", _StubClient([]))
    assert idx["texts"] == []
    assert search_bm25(idx, "cualquier cosa") == []
