import json
from types import SimpleNamespace

import pytest

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


def test_input_check_rejects_duplicate_source_stems(monkeypatch, tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "same.md").write_text("one", encoding="utf-8")
    (tmp_path / "b" / "same.txt").write_text("two", encoding="utf-8")
    monkeypatch.delenv("OCEANGRAPH_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("OCEANGRAPH_INPUT_DIR", raising=False)
    monkeypatch.setattr(
        config,
        "get_paths_config",
        lambda: {"input_pdf_dir": str(tmp_path), "output_dir": str(tmp_path / "out")},
    )

    result = preflight.check_input_data()

    assert result.status is preflight.CheckStatus.FAIL
    assert "unique stems" in result.message


def test_semantic_chunking_uses_corpus_route(monkeypatch):
    stages = []

    def fail_after_recording(prompt, stage="default", **kwargs):
        stages.append(stage)
        raise RuntimeError("stop after route capture")

    monkeypatch.setattr(chunker, "call_llm_simple", fail_after_recording)

    with pytest.raises(RuntimeError, match="stop after route capture"):
        chunker.chunk_with_windows("A short ocean-science test document.")

    assert stages == ["corpus"]


def test_disabled_evaluation_skips_metrics_embedding_check(monkeypatch):
    called = []

    def passed(name):
        return lambda: preflight.CheckResult(
            name=name,
            status=preflight.CheckStatus.PASS,
            message="ok",
        )

    for name, attribute in (
        ("config", "check_config"),
        ("api", "check_api_key"),
        ("input", "check_input_data"),
        ("output", "check_output_directory"),
        ("gpu", "check_gpu_availability"),
        ("llm", "check_llm_call"),
        ("verifier", "check_vlm_call"),
        ("embedding", "check_embedding_model"),
        ("reranker", "check_reranker"),
    ):
        monkeypatch.setattr(preflight, attribute, passed(name))

    def metrics_check():
        called.append(True)
        return passed("metrics")()

    monkeypatch.setattr(preflight, "check_metrics_embeddings", metrics_check)
    monkeypatch.setattr(config, "load_config", lambda: {"evaluation": {"run_evaluation": False}})

    all_passed, results = preflight.run_preflight_checks(
        quiet=True,
        check_timeout_seconds=1,
    )

    assert all_passed is True
    assert called == []
    assert any(result.name == "Metrics Embeddings" and result.status is preflight.CheckStatus.SKIP for result in results)
