import json
from types import SimpleNamespace

from oceangraph.core import config, llm
from oceangraph.pipeline import chunker
from oceangraph.utils import preflight


def test_api_key_check_uses_routed_profiles(monkeypatch):
    profile = SimpleNamespace(api_key="x" * 20, model_name=lambda: "routed-model")
    stages = []

    def get_profile(stage):
        stages.append(stage)
        return profile

    monkeypatch.setattr(llm, "_get_model_profile", get_profile)

    result = preflight.check_api_key()

    assert result.status is preflight.CheckStatus.PASS
    assert stages == ["generation", "verification"]


def test_preflight_calls_generation_and_text_verification(monkeypatch):
    stages = []

    def call_llm(prompt, stage="default", **kwargs):
        stages.append(stage)
        return "OK"

    monkeypatch.setattr(llm, "call_llm_simple", call_llm)
    monkeypatch.setattr(
        llm,
        "get_model_route_info",
        lambda stage: {"backend": "OPENAI", "model": stage},
    )
    monkeypatch.setattr(config, "is_text_only_mode", lambda: True)

    assert preflight.check_llm_call().status is preflight.CheckStatus.PASS
    assert preflight.check_vlm_call().status is preflight.CheckStatus.PASS
    assert stages == ["generation", "verification"]


def test_input_check_accepts_resumable_output(monkeypatch, tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "chunks.json").write_text(
        json.dumps([{"chunk_id": "1"}, {"chunk_id": "2"}]),
        encoding="utf-8",
    )
    monkeypatch.setenv("OCEANGRAPH_OUTPUT_DIR", str(output_dir))
    monkeypatch.setattr(config, "get_paths_config", lambda: {})

    result = preflight.check_input_data()

    assert result.status is preflight.CheckStatus.PASS
    assert result.details["source"] == "output_checkpoint"
    assert result.details["count"] == 2


def test_semantic_chunking_uses_corpus_route(monkeypatch):
    stages = []

    def fail_after_recording(prompt, stage="default", **kwargs):
        stages.append(stage)
        raise RuntimeError("stop after route capture")

    monkeypatch.setattr(chunker, "call_llm_simple", fail_after_recording)

    chunks, _ = chunker.chunk_with_windows("A short ocean-science test document.")

    assert chunks == []
    assert stages == ["corpus"]
