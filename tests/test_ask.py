def test_ask_returns_sources():
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    r = client.get("/ask", params={"q": "gatos", "lang": "es"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and len(data["answer"]) > 0
    assert "sources" in data and len(data["sources"]) > 0
    assert any(f"[{i}]" in data["answer"] for i in range(1, 6))  # cita alguna fuente


def test_ask_reports_stage_timing():
    from fastapi.testclient import TestClient

    from api.main import app

    r = TestClient(app).get("/ask", params={"q": "política de gastos de viaje", "lang": "es"})
    assert r.status_code == 200
    t = r.json()["timing"]
    for k in ("embed", "search", "answer", "total"):
        assert k in t, f"falta la etapa '{k}' en timing"
    assert t["total"] >= max(t["embed"], t["search"], t["answer"])
