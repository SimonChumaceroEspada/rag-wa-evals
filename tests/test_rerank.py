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


def test_rerank_honors_candidate_cap(monkeypatch):
    monkeypatch.setenv("RERANK_MAX_DOCS", "6")
    seen = []

    def spy(q, docs):
        seen.append(len(docs))
        return [float(i) for i in range(len(docs))]

    docs = [{"text": f"doc {i}", "source": f"s{i}", "score": 1.0} for i in range(19)]
    out = rerank("q", docs, top_n=5, score_fn=spy)
    assert seen == [6], f"el cap RERANK_MAX_DOCS=6 no se aplicó (vio {seen})"
    assert len(out) == 5


def test_rerank_scorer_uses_short_timeout(monkeypatch):
    import openai
    import pytest

    import src.rerank as r

    seen = {}

    def fake_openai(**kw):
        seen.update(kw)
        raise RuntimeError("corte corto")

    monkeypatch.setattr(openai, "OpenAI", fake_openai)
    with pytest.raises(RuntimeError):
        r._score_with("http://x", "k", "m", "q", [{"text": "a"}])
    assert seen.get("timeout", 999) <= 15, "timeout del scorer demasiado alto"


def test_rerank_scorer_disables_nim_reasoning(monkeypatch):
    import openai

    import src.rerank as r

    seen = {}

    class Fake:
        def __init__(self, **kw):
            self.chat = self
            self.completions = self

        def create(self, **kw):
            seen.update(kw)

            class Msg:
                content = "[1]"

            class Ch:
                message = Msg()

            class R:
                choices = [Ch()]

            return R()

    monkeypatch.setattr(openai, "OpenAI", Fake)
    r._score_with("https://integrate.api.nvidia.com/v1", "k", "m", "q", [{"text": "a"}])
    assert seen["extra_body"]["reasoning"]["effort"] == "none", "rerank NIM sin effort=none tarda 10-60s"


def test_rerank_uses_fast_provider_first(monkeypatch):
    import src.rerank as r

    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "fr")
    calls = []

    def spy(base, key, model, q, docs):
        calls.append("nvidia" in base)
        return [1.0] * len(docs)

    monkeypatch.setattr(r, "_score_with", spy)
    r.llm_score_fn("q", [{"text": "a"}])
    assert calls == [True], f"orden de proveedores {calls}: NIM con effort=none es rápido y fiable"
