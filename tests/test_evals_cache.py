import json
import sys


def test_fresh_refreshes_stale_cache(tmp_path, monkeypatch):
    import evals.run_ragas as R

    q0 = json.loads(open("evals/qa_es.jsonl", encoding="utf-8").readline())["q"]
    cache_p = tmp_path / "c.json"
    cache_p.write_text(json.dumps({q0: {"answer": "STALE", "sources": []}}), encoding="utf-8")
    monkeypatch.setattr(R, "qdrant_up", lambda: True)
    monkeypatch.setattr(
        R, "live_ask",
        lambda client, q, lang="es": {
            "answer": "FRESH [1]",
            "sources": [{"text": "t", "source": "SLA.pdf", "score": 0.02}],
        },
    )
    monkeypatch.setattr(
        sys, "argv",
        ["run_ragas", "--fresh", "--n", "1", "--cache", str(cache_p),
         "--out", str(tmp_path / "o.json")],
    )
    R.main()
    got = json.loads(cache_p.read_text(encoding="utf-8"))[q0]["answer"]
    assert got == "FRESH [1]", f"--fresh no refrescó el caché, quedó: {got[:40]}"


def test_no_fresh_keeps_cache(tmp_path, monkeypatch):
    import evals.run_ragas as R

    q0 = json.loads(open("evals/qa_es.jsonl", encoding="utf-8").readline())["q"]
    cache_p = tmp_path / "c.json"
    cache_p.write_text(json.dumps({q0: {"answer": "STALE", "sources": []}}), encoding="utf-8")
    monkeypatch.setattr(R, "qdrant_up", lambda: True)
    monkeypatch.setattr(
        R, "live_ask",
        lambda client, q, lang="es": {
            "answer": "FRESH [1]",
            "sources": [{"text": "t", "source": "SLA.pdf", "score": 0.02}],
        },
    )
    monkeypatch.setattr(
        sys, "argv",
        ["run_ragas", "--n", "1", "--cache", str(cache_p),
         "--out", str(tmp_path / "o.json")],
    )
    R.main()
    got = json.loads(cache_p.read_text(encoding="utf-8"))[q0]["answer"]
    assert got == "STALE", "sin --fresh debe reusar el caché"
