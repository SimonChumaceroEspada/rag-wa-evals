import re

from api.main import answer_leaked, extractive, strip_reasoning


def test_strip_reasoning_keeps_final_answer():
    raw = ("Thinking Process:\n1. Analyze User Input: uptime\n\n"
           "Final Answer: AcmeTech garantiza 99.9% de uptime [1].")
    assert strip_reasoning(raw) == "AcmeTech garantiza 99.9% de uptime [1]."


def test_strip_reasoning_keeps_last_clean_paragraph():
    raw = "Thinking process: analyze user input\n\nAcmeTech ofrece 99.9% de uptime a Enterprise [1]."
    out = strip_reasoning(raw)
    assert "99.9%" in out
    assert "thinking" not in out.lower()


def test_strip_reasoning_passthrough_clean():
    assert strip_reasoning("AcmeTech ofrece 99.9% [1].") == "AcmeTech ofrece 99.9% [1]."


def test_strip_reasoning_empty_when_all_reasoning():
    assert strip_reasoning("Thinking Process:\n1. Analyze User Input: bla") == ""


def test_llm_chain_skips_reasoning_only_candidate(monkeypatch):
    import api.main as m

    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi_test")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    seen = []

    def fake_chat(system, user, base_url, api_key, model, tokens):
        seen.append(base_url)
        if "groq" in base_url:
            return "Thinking Process:\n1. Analyze User Input: uptime"
        return "AcmeTech garantiza 99.9% de uptime a Enterprise [1]."

    monkeypatch.setattr(m, "_chat", fake_chat)
    out = m.llm_answer("¿uptime?", "es", "[1] AcmeTech garantiza 99.9% de uptime a Enterprise.")
    assert "99.9%" in out
    assert seen == ["https://api.groq.com/openai/v1", "https://integrate.api.nvidia.com/v1"]


def test_llm_chain_falls_back_to_extractive(monkeypatch):
    import api.main as m

    monkeypatch.setenv("GROQ_API_KEY", "gsk_test")
    monkeypatch.setenv("NVIDIA_API_KEY", "")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")

    def boom(*a, **k):
        raise RuntimeError("caído")

    monkeypatch.setattr(m, "_chat", boom)
    out = m.llm_answer("uptime", "es", "[1] AcmeTech ofrece 99.9% de uptime.")
    assert out.startswith("Según las fuentes [1]:")
    assert "99.9%" in out


def test_thinking_leak_detected():
    assert answer_leaked("Here's a thinking process:\n1. Analyze User Input: bla") is True
    assert answer_leaked("AcmeTech garantiza 99.9% de uptime [2]") is False


def test_extractive_always_cites():
    a = extractive("es", "¿qué uptime ofrece AcmeTech?",
                   "[1] AcmeTech ofrece 99.9% de uptime a Enterprise. Fin.")
    assert "99.9% de uptime" in a
    assert a.endswith("[1]")


def test_extractive_does_not_echo_context_marker():
    a = extractive("es", "uptime", "[1] AcmeTech ofrece 99.9% de uptime.")
    assert "[1] [1]" not in a
    assert not re.search(r"\[\d+\]:\s*\[\d+\]", a)


def test_extractive_head_matches_lang():
    ctx = "[1] AcmeTech guarantees 99.9% uptime."
    assert extractive("es", "uptime", ctx).startswith("Según las fuentes")
    assert extractive("en", "uptime", ctx).startswith("According to the sources")


def test_extractive_never_cuts_mid_word_and_stays_short():
    ctx = "[1] " + " ".join(f"palabra{i}" for i in range(60))
    a = extractive("en", "palabra1", ctx)
    body = a.split(": ", 1)[1].rsplit(" [1]", 1)[0]
    assert len(a) < 520
    assert not body.rstrip("…").endswith(("palabra", "palabr"))


def test_extractive_prefers_sentence_with_query_terms():
    ctx = ("[1] El clima hoy es soleado en Lima. "
           "AcmeTech garantiza 99.9% de uptime a los clientes Enterprise. "
           "Los gatos duermen mucho.")
    a = extractive("es", "¿qué uptime garantiza AcmeTech?", ctx)
    assert "99.9% de uptime" in a
    assert "clima" not in a


def test_word_count_leak_detected():
    raw = 'Count words: Let me count: "AcmeTech\'s(1) coding(2) practices(3)"'
    assert answer_leaked(raw) is True


def test_answer_token_budget_is_small(monkeypatch):
    import api.main as m

    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi_test")
    monkeypatch.setenv("FREELLMAPI_API_KEY", "")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    seen = []
    monkeypatch.setattr(
        m, "_chat",
        lambda system, user, base, key, model, tokens: (seen.append(tokens), "Respuesta limpia [1].")[1],
    )
    m.llm_answer("uptime", "es", "[1] AcmeTech ofrece 99.9% de uptime.")
    assert seen and seen[0] <= 400, f"presupuesto de tokens {seen[0]} — genera respuestas que divagan"


def test_strip_reasoning_rejects_leftover_thinking_steps():
    raw = ("Here's a thinking process:\n\n1. **Analyze User Input:**\n"
           "   - User asks: cuántos días de vacaciones hay\n\n"
           "2. **Scan Context for Vacation/PTO:**\n"
           "   - Document [3] is Leave_Policy, clearly the relevant one.\n"
           "   - In [3], section 1: Los empleados acumulan 22 días de PTO al año.")
    assert strip_reasoning(raw) == "", "un paso del razonamiento no puede pasar por respuesta"


def test_chat_disables_nim_reasoning(monkeypatch):
    import openai

    import api.main as m

    seen = {}

    class Fake:
        def __init__(self, **kw):
            self.chat = self
            self.completions = self

        def create(self, **kw):
            seen.update(kw)

            class Msg:
                content = "ok"

            class Ch:
                message = Msg()

            class R:
                choices = [Ch()]

            return R()

    monkeypatch.setattr(openai, "OpenAI", Fake)
    assert m._chat("s", "u", "https://integrate.api.nvidia.com/v1", "k", "m", 400) == "ok"
    assert seen["extra_body"]["reasoning"]["effort"] == "none", "NIM sin effort=none divaga y cuesta 16-60s"
