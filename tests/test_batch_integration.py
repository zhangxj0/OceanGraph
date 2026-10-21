import json
import threading

import pytest
import yaml

from oceangraph.batch.config import load_routes
from oceangraph.batch.run import Client, export_dataset, process_source
from oceangraph.batch.state import State, BudgetStop


def test_two_provider_batch_exports_provenance_and_accounts_usage(tmp_path, monkeypatch):
    config = {"models": {"profiles": {
        "generator": {"model": "generator-one", "base_url": "https://gen.example/v1", "api_key_env": "GEN_KEY", "structured_output": True},
        "verifier": {"model": "verifier-two", "url": "https://ver.example/v2/chat/completions", "api_key_env": "VER_KEY", "structured_output": True},
    }}}
    path = tmp_path / "llm.yaml"
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    monkeypatch.setenv("GEN_KEY", "generator-secret")
    monkeypatch.setenv("VER_KEY", "verifier-secret")
    seen = []

    # A fake HTTP transport exercises the real Client, state, selection and exports.
    def fake_post(url, json, headers, timeout, allow_redirects):
        seen.append((url, json, headers, timeout, allow_redirects))
        if json["model"] == "generator-one":
            reply = {"qa_pairs": [{"question": "Which nutrient does the bloom-forming diatom at station Alpha consume?",
                                   "answer": "Silicate", "question_type": "bridge", "answer_type": "entity"}]}
        else:
            reply = {"reviews": [{"candidate_id": "q1", "verdict": "ACCEPT", "quality": "clear_multi_step",
                                   "reason": "The organism and nutrient are linked by two source statements.",
                                   **{k: True for k in ("question_standalone", "single_target", "answer_supported", "domain_relevant", "multihop_plausible", "arithmetic_consistent", "conditions_consistent")}}]}
        class Response:
            status_code = 200
            def json(self):
                return {"usage": {"prompt_tokens": 40, "completion_tokens": 20},
                        "choices": [{"finish_reason": "stop", "message": {"content": __import__('json').dumps(reply)}}]}
        return Response()

    monkeypatch.setattr("oceangraph.batch.run.requests.post", fake_post)
    state = State(tmp_path / "run.sqlite", target=1)
    try:
        source = {"id": "doc-one", "title": "Marine bloom at Alpha", "topic": "ecology_plankton", "source_url": "https://source.example/paper", "doi": "example-doi",
                  "chunks": ["The bloom at station Alpha is formed by a diatom.", "This diatom consumes silicate in coastal seawater."]}
        state.add_sources([source])
        client = Client(state, load_routes(path, require_keys=True), threading.Event())
        assert process_source(source, client, state, lambda *args: []) == 1
        summary = export_dataset(state, tmp_path, True, True)
        assert summary["completed"] is True
        assert state.totals()["input_reported"] == 80
        assert state.totals()["output_reported"] == 40
        assert seen[0][0] == "https://gen.example/v1/chat/completions"
        assert seen[1][0] == "https://ver.example/v2/chat/completions"
        assert seen[0][2]["Authorization"] == "Bearer generator-secret"
        assert seen[1][2]["Authorization"] == "Bearer verifier-secret"
        routes = state.db.execute("SELECT metadata FROM call_routes ORDER BY call_id").fetchall()
        assert [json.loads(r[0])["model"] for r in routes] == ["generator-one", "verifier-two"]
        exported = json.loads((tmp_path / "qa_20000.jsonl").read_text())
        assert exported["model_provenance"]["verification"]["model"] == "verifier-two"
        split_rows = [json.loads(line) for p in (tmp_path/"training").glob("*.jsonl") if p.name in {"train.jsonl", "dev.jsonl", "test.jsonl"} for line in p.read_text().splitlines()]
        assert len(split_rows) == 1
        assert split_rows[0]["metadata"]["model_provenance"]["generation"]["model"] == "generator-one"
        assert "generator-secret" not in (tmp_path / "qa_20000.jsonl").read_text()
    finally:
        state.close()


def test_expired_client_does_not_reserve_or_send(tmp_path, monkeypatch):
    state = State(tmp_path / "run.sqlite")
    monkeypatch.setattr("oceangraph.batch.run.requests.post", lambda *a, **k: pytest.fail("Network call"))
    try:
        from oceangraph.providers.router import ModelProfile
        profile = ModelProfile(name="test", backend="OPENAI", model="test", url="https://test.example/chat/completions")
        client = Client(state, {s: profile for s in ("generation", "verification")}, threading.Event(), deadline=0)
        with pytest.raises(BudgetStop):
            client.call("prompt", "generation", "doc")
        assert state.totals()["requests"] == 0
    finally:
        state.close()
