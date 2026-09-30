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

    # sin Gemini configurado el primer candidato sigue siendo NIM.
    # "" en vez de delenv: llm_score_fn llama a load_dotenv() y lo repondría.
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_CHAT_MODEL", "")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "fr")
    calls = []

    def spy(base, key, model, q, docs):
        calls.append("nvidia" in base)
        return [1.0] * len(docs)

    monkeypatch.setattr(r, "_score_with", spy)
    r.llm_score_fn("q", [{"text": "a"}])
    assert calls == [True], f"orden de proveedores {calls}: NIM con effort=none es rápido y fiable"


def test_rerank_prefers_gemini_when_configured(monkeypatch):
    import src.rerank as r

    monkeypatch.setenv("GEMINI_API_KEY", "gk")
    monkeypatch.setenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "fr")
    calls = []

    def spy(base, key, model, q, docs):
        calls.append(base)
        return [1.0] * len(docs)

    monkeypatch.setattr(r, "_score_with", spy)
    r.llm_score_fn("q", [{"text": "a"}])
    assert "generativelanguage" in calls[0], f"gemini debía ir primero, orden: {calls}"
    assert len(calls) == 1, f"gemini contestó y aun así probó otro: {calls}"


def test_rerank_falls_back_when_gemini_fails(monkeypatch):
    import src.rerank as r

    monkeypatch.setenv("GEMINI_API_KEY", "gk")
    monkeypatch.setenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash-lite")
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "fr")
    calls = []

    def spy(base, key, model, q, docs):
        calls.append(base)
        if "generativelanguage" in base:
            raise RuntimeError("429")
        return [1.0] * len(docs)

    monkeypatch.setattr(r, "_score_with", spy)
    scores = r.llm_score_fn("q", [{"text": "a"}])
    assert scores == [1.0], "debía degradar al siguiente proveedor"
    assert "generativelanguage" in calls[0] and "nvidia" in calls[1], f"orden: {calls}"


def test_rerank_skips_gemini_without_model(monkeypatch):
    import src.rerank as r

    monkeypatch.setenv("GEMINI_API_KEY", "gk")
    monkeypatch.setenv("GEMINI_CHAT_MODEL", "")  # "" = load_dotenv no lo repone
    monkeypatch.setenv("NVIDIA_API_KEY", "nv")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "")
    calls = []

    def spy(base, key, model, q, docs):
        calls.append(base)
        return [1.0] * len(docs)

    monkeypatch.setattr(r, "_score_with", spy)
    r.llm_score_fn("q", [{"text": "a"}])
    assert all("generativelanguage" not in b for b in calls), (
        "sin GEMINI_CHAT_MODEL no debe probar un modelo por su cuenta"
    )
