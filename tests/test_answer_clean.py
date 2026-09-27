from api.main import answer_leaked, extractive


def test_thinking_leak_detected():
    assert answer_leaked("Here's a thinking process:\n1. Analyze User Input: bla") is True
    assert answer_leaked("AcmeTech garantiza 99.9% de uptime [2]") is False


def test_extractive_always_cites():
    a = extractive("es", "[1] texto del chunk")
    assert "[1]" in a and "texto del chunk" in a
