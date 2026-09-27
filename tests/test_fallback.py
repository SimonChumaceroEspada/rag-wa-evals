from src.fallback import call_with_fallback


def test_primary_ok_no_fallback():
    calls = []

    def primary():
        calls.append("p")
        return "P"

    def fallback():
        calls.append("f")
        return "F"

    assert call_with_fallback(primary, fallback, label="t") == ("P", "primary")
    assert calls == ["p"]


def test_fallback_on_429():
    def primary():
        raise RuntimeError("429 rate limit")

    def fallback():
        return "F"

    assert call_with_fallback(primary, fallback, label="t") == ("F", "fallback")
