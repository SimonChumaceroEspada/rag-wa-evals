def test_ask_returns_sources():
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    r = client.get("/ask", params={"q": "gatos", "lang": "es"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data and len(data["answer"]) > 0
    assert "sources" in data and len(data["sources"]) > 0
    assert "[1]" in data["answer"]
