import json
import sys
import types
from types import SimpleNamespace

import pytest

from oceangraph import OceanGraph
from oceangraph import cli
from oceangraph.utils import preflight
from oceangraph.utils.scheduling import bounded_submission_size


def test_preflight_cli_exits_nonzero_when_checks_fail(monkeypatch):
    monkeypatch.setattr(cli, "parse_args", lambda: SimpleNamespace(verbose=False, preflight=True))
    monkeypatch.setattr(cli, "setup_environment", lambda args: None)
    monkeypatch.setattr(preflight, "run_preflight_checks", lambda: (False, []))

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 1


def test_generation_cli_exits_nonzero_when_pipeline_stops(monkeypatch, tmp_path):
    args = SimpleNamespace(
        verbose=False,
        preflight=False,
        input=str(tmp_path),
        output=str(tmp_path / "output"),
        backend="openai",
        num_qa_pairs=1,
        no_strict_multihop=False,
    )
    fake_engine = types.ModuleType("oceangraph.engine")
    fake_engine.run_pipeline = lambda: False
    monkeypatch.setitem(sys.modules, "oceangraph.engine", fake_engine)
    monkeypatch.setattr(cli, "parse_args", lambda: args)
    monkeypatch.setattr(cli, "setup_environment", lambda parsed: None)
    monkeypatch.setattr(cli, "validate_args", lambda parsed: [])
    monkeypatch.setattr(cli, "write_run_metadata", lambda parsed: None)

    with pytest.raises(SystemExit) as exc_info:
        cli.main()

    assert exc_info.value.code == 1


def test_public_api_does_not_collect_stale_results_after_failed_run(monkeypatch, tmp_path):
    fake_engine = types.ModuleType("oceangraph.engine")
    fake_engine.run_pipeline = lambda config: False
    monkeypatch.setitem(sys.modules, "oceangraph.engine", fake_engine)
    pipeline = OceanGraph(output_dir=str(tmp_path), backend="ollama")

    with pytest.raises(RuntimeError, match="mandatory preflight"):
        pipeline.run()


def test_submission_size_is_bounded_by_remaining_target():
    assert bounded_submission_size(100, 8, 1) == 1
    assert bounded_submission_size(100, 8, 3) == 3
    assert bounded_submission_size(100, 8, 20) == 8
    assert bounded_submission_size(3, 8, None) == 3
    assert bounded_submission_size(3, 8, 0) == 0


def test_expensive_preflight_timeout_terminates_isolated_check(monkeypatch):
    def timeout(*args, **kwargs):
        raise preflight.subprocess.TimeoutExpired(cmd=args[0], timeout=0.01)

    monkeypatch.setattr(preflight.subprocess, "run", timeout)
    result = preflight._run_check_in_subprocess("embedding", 0.01)

    assert result.status is preflight.CheckStatus.FAIL
    assert "timed out" in result.message
    assert result.details["isolated_process"] is True


def test_isolated_preflight_receives_runtime_config(monkeypatch):
    captured = {}

    def completed(*args, **kwargs):
        captured.update(kwargs["env"])
        payload = {
            "name": "Embedding Model",
            "status": "PASS",
            "message": "ok",
            "details": {},
            "duration_ms": 1,
        }
        return SimpleNamespace(
            returncode=0,
            stdout=preflight._RESULT_PREFIX + json.dumps(payload),
            stderr="",
        )

    monkeypatch.setattr(preflight.subprocess, "run", completed)
    result = preflight._run_check_in_subprocess(
        "embedding",
        1,
        runtime_config={"embedding": {"model": "custom-model"}},
    )

    assert result.status is preflight.CheckStatus.PASS
    assert "custom-model" in captured["OCEANGRAPH_PREFLIGHT_CONFIG_JSON"]


def test_preflight_skips_paid_checks_after_local_prerequisite_failure(monkeypatch):
    expensive_calls = []

    def result(name, status=preflight.CheckStatus.PASS):
        return lambda: preflight.CheckResult(name=name, status=status, message=name)

    monkeypatch.setattr(
        preflight,
        "check_config",
        result("config", preflight.CheckStatus.FAIL),
    )
    for attribute in (
        "check_api_key",
        "check_input_data",
        "check_output_directory",
        "check_gpu_availability",
    ):
        monkeypatch.setattr(preflight, attribute, result(attribute))
    for attribute in (
        "check_llm_call",
        "check_vlm_call",
        "check_embedding_model",
        "check_reranker",
        "check_metrics_embeddings",
    ):
        monkeypatch.setattr(
            preflight,
            attribute,
            lambda attribute=attribute: expensive_calls.append(attribute),
        )

    all_passed, results = preflight.run_preflight_checks(
        quiet=True,
        check_timeout_seconds=1,
    )

    assert all_passed is False
    assert expensive_calls == []
    assert any(result.status is preflight.CheckStatus.SKIP for result in results)


def test_preflight_stops_after_first_expensive_failure(monkeypatch):
    calls = []

    def passed(name):
        return lambda: preflight.CheckResult(
            name=name,
            status=preflight.CheckStatus.PASS,
            message="ok",
        )

    for attribute in (
        "check_config",
        "check_api_key",
        "check_input_data",
        "check_output_directory",
        "check_gpu_availability",
    ):
        monkeypatch.setattr(preflight, attribute, passed(attribute))

    def failed_llm():
        calls.append("llm")
        return preflight.CheckResult(
            name="LLM API",
            status=preflight.CheckStatus.FAIL,
            message="failed",
        )

    monkeypatch.setattr(preflight, "check_llm_call", failed_llm)
    for attribute in (
        "check_vlm_call",
        "check_embedding_model",
        "check_reranker",
        "check_metrics_embeddings",
    ):
        monkeypatch.setattr(
            preflight,
            attribute,
            lambda attribute=attribute: calls.append(attribute),
        )

    all_passed, _ = preflight.run_preflight_checks(
        quiet=True,
        check_timeout_seconds=1,
    )

    assert all_passed is False
    assert calls == ["llm"]
