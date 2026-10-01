from evals.run_ragas import live_ask, qa_path_for


def test_qa_path_for_lang():
    assert str(qa_path_for("en")).endswith("qa_en.jsonl")
    assert str(qa_path_for("es")).endswith("qa_es.jsonl")


def test_live_ask_passes_lang():
    seen = {}

    class FakeResp:
        status_code = 200

        def json(self):
            return {"answer": "a [1]", "sources": []}

    class FakeClient:
        def get(self, path, params=None):
            seen.update(params or {})
            return FakeResp()

    out = live_ask(FakeClient(), "what uptime?", lang="en")
    assert seen.get("lang") == "en", f"el runner quemó lang=es: {seen}"
    assert out["answer"] == "a [1]"
