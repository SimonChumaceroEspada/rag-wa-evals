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
