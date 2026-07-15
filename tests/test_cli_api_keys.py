from argparse import Namespace
import os

import yaml

from oceangraph.cli import setup_environment, validate_args


def _write_config(path):
    path.write_text(
        yaml.safe_dump(
            {
                "models": {
                    "profiles": {
                        "verifier": {
                            "backend": "OPENAI",
                            "api_key_env": "DEEPSEEK_API_KEY",
                        }
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_validate_args_accepts_stage_routed_api_key(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    args = Namespace(
        input=None,
        preflight=False,
        backend="openai",
        api_key=None,
        config=str(config_path),
    )

    assert validate_args(args) == []


def test_setup_environment_maps_cli_key_to_routed_profile(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    args = Namespace(
        config=str(config_path),
        api_key="test-key",
        backend="openai",
        model=None,
        no_counterfactual_verification=False,
        input=None,
        output=None,
        num_qa_pairs=1,
        max_workers=1,
        embedding_model="bge_m3",
        offline_models=False,
        reranker_model="text_embedding",
        max_depth=2,
        no_strict_multihop=False,
        min_supporting_chunks=2,
        no_jsonl=False,
        deduplication=False,
        evaluation=False,
    )

    setup_environment(args)

    assert os.environ["OPENAI_API_KEY"] == "test-key"
    assert os.environ["DEEPSEEK_API_KEY"] == "test-key"
