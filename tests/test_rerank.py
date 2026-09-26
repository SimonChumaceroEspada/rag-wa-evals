from src.rerank import rerank


def fake_scorer(q, docs):
    # finge: el último doc es el más relevante
    return list(range(len(docs)))


def test_rerank_reorders_and_trims():
    docs = [
        {"text": f"doc {i}", "source": f"s{i}", "score": 1.0}
        for i in range(8)
    ]
    out = rerank("pregunta", docs, top_n=5, score_fn=fake_scorer)
    assert [d["text"] for d in out] == [f"doc {i}" for i in (7, 6, 5, 4, 3)]


def test_rerank_fallback_keeps_rrf_order():
    def boom(q, docs):
        raise RuntimeError("llm caído")

    docs = [{"text": f"doc {i}", "source": f"s{i}", "score": 1.0 - i * 0.1} for i in range(4)]
    out = rerank("pregunta", docs, top_n=3, score_fn=boom)
    assert [d["text"] for d in out] == ["doc 0", "doc 1", "doc 2"]
