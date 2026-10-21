import importlib
import json
from pathlib import Path

import pytest
import yaml

from oceangraph.providers.router import StageModelRouter
from oceangraph.core.config import clear_runtime_config, load_config


def config():
    return {"models": {"profiles": {
        "generator": {"backend": "OPENAI", "model": "glm-test", "base_url": "https://glm.example/v1/", "api_key_env": "GEN_KEY", "max_output_tokens": 32768, "structured_output": True, "extra_body": {"reasoning_effort": "low"}},
        "verifier": {"backend": "OPENAI", "model": "deepseek-test", "base_url": "https://ds.example", "api_key_env": "VER_KEY", "max_output_tokens": 4096, "structured_output": True, "extra_body": {"thinking": {"type": "enabled"}, "reasoning_effort": "high"}},
    }, "stages": {"generation": "generator", "verification": "verifier"}}}


def router(value):
    return StageModelRouter.from_config(value, fallback_backend="OPENAI", fallback_url="https://fallback.example/chat/completions", fallback_llm_model="fallback", fallback_vlm_model="fallback")


def test_base_url_routes_preserve_paths():
    r = router(config())
    assert r.resolve("generation").url == "https://glm.example/v1/chat/completions"
    assert r.resolve("verification").url == "https://ds.example/chat/completions"


def test_ambiguous_url_fields_fail():
    c = config()
    c["models"]["profiles"]["generator"]["url"] = "https://other.example/chat/completions"
    with pytest.raises(ValueError, match="url"):
        router(c)


def test_external_config_applies_without_primary_config(tmp_path, monkeypatch):
    path = tmp_path / "models.yaml"
    path.write_text(yaml.safe_dump(config()), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OCEANGRAPH_LLM_CONFIG", str(path))
    clear_runtime_config()
    try:
        loaded = load_config(str(tmp_path / "absent.yaml"))
        assert loaded.get("models") == config()["models"]
    finally:
        clear_runtime_config()


def test_batch_config_routes_keys_and_limits(tmp_path, monkeypatch):
    from oceangraph.batch.config import load_routes, request_for
    path = tmp_path / "models.yaml"
    path.write_text(yaml.safe_dump(config()), encoding="utf-8")
    monkeypatch.setenv("GEN_KEY", "generator-secret")
    monkeypatch.setenv("VER_KEY", "verifier-secret")
    routes = load_routes(path)
    gen = request_for(routes, "generation", "Return JSON", 8192)
    ver = request_for(routes, "verification", "Review JSON", 8192)
    assert gen[0] == "https://glm.example/v1/chat/completions"
    assert ver[0] == "https://ds.example/chat/completions"
    assert gen[1]["Authorization"] == "Bearer generator-secret"
    assert ver[1]["Authorization"] == "Bearer verifier-secret"
    assert gen[2]["model"] == "glm-test"
    assert ver[2]["model"] == "deepseek-test"
    assert gen[2]["max_tokens"] == 8192
    assert ver[2]["max_tokens"] == 4096
    assert "secret" not in json.dumps(gen[3])


def test_batch_cannot_override_messages_model_or_budget(tmp_path):
    from oceangraph.batch.config import load_routes
    for field in ("model", "messages", "max_tokens", "max_completion_tokens", "stream", "n"):
        c = config()
        c["models"]["profiles"]["generator"]["extra_body"][field] = 99
        path = tmp_path / "bad.yaml"
        path.write_text(yaml.safe_dump(c), encoding="utf-8")
        with pytest.raises(ValueError, match="extra_body"):
            load_routes(path)


def test_batch_missing_verifier_key_does_not_fallback(tmp_path, monkeypatch):
    from oceangraph.batch.config import load_routes
    path = tmp_path / "models.yaml"
    path.write_text(yaml.safe_dump(config()), encoding="utf-8")
    monkeypatch.setenv("GEN_KEY", "generator-secret")
    monkeypatch.delenv("VER_KEY", raising=False)
    with pytest.raises(ValueError, match="VER_KEY"):
        load_routes(path, require_keys=True)


def test_check_config_needs_no_posix_lock_network_or_output(tmp_path, monkeypatch, capsys):
    from oceangraph.batch import run
    path = tmp_path / "models.yaml"
    path.write_text(yaml.safe_dump(config()), encoding="utf-8")
    output = tmp_path / "never-created"
    monkeypatch.setenv("GEN_KEY", "generator-secret")
    monkeypatch.setenv("VER_KEY", "verifier-secret")
    monkeypatch.setattr(run, "fcntl", None)
    monkeypatch.setattr(run.requests, "post", lambda *a, **kw: pytest.fail("Unexpected network call"))
    monkeypatch.setattr("sys.argv", ["run", "--llm-config", str(path), "--output", str(output), "--check-config"])
    run.main()
    captured = capsys.readouterr().out
    assert "glm-test" in captured and "deepseek-test" in captured
    assert "generator-secret" not in captured and "verifier-secret" not in captured
    assert not output.exists()
