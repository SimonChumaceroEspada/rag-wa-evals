import time

import api.keepalive as k


def test_keepalive_disabled_without_url():
    assert k.start_keepalive("") is None
    assert k.start_keepalive(None) is None
    assert k.start_keepalive("   ") is None


def test_keepalive_pings_on_interval():
    urls = []
    k.start_keepalive("https://x/openapi.json", interval=0.05,
                      ping_fn=lambda u: urls.append(u))
    time.sleep(0.2)
    assert urls, "el keepalive no pegó en ningún intervalo"
    assert urls[0] == "https://x/openapi.json"
    assert len(urls) >= 2, f"esperaba varios pings, llegaron {len(urls)}"


def test_keepalive_survives_failed_pings():
    calls = []

    def flaky(url):
        calls.append(url)
        if len(calls) < 3:
            raise RuntimeError("red caída")

    k.start_keepalive("https://x", interval=0.03, ping_fn=flaky)
    time.sleep(0.3)
    assert len(calls) >= 4, "un ping fallido mató el loop: Render volvería a dormirse"


def test_keepalive_interval_is_capped_below_render_sleep():
    assert k.clamp_interval(3600) <= 840, "intervalo > 15 min no evita que Render duerma"


def test_api_starts_keepalive_from_env(monkeypatch):
    import api.main as m

    monkeypatch.setenv("KEEPALIVE_URL", "https://rag-wa-evals.onrender.com")
    monkeypatch.setenv("KEEPALIVE_INTERVAL", "600")
    seen = []
    monkeypatch.setattr(m, "start_keepalive", lambda url, interval=600: seen.append((url, interval)))
    m.start_services()
    assert seen == [("https://rag-wa-evals.onrender.com", 600)]


def test_api_keepalive_off_without_env(monkeypatch):
    import api.main as m

    monkeypatch.delenv("KEEPALIVE_URL", raising=False)
    seen = []
    monkeypatch.setattr(m, "start_keepalive", lambda url, interval=600: seen.append(url))
    m.start_services()
    assert seen == [] or seen == [""], "sin KEEPALIVE_URL no debe lanzar thread"
