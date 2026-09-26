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
