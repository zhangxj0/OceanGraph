from argparse import Namespace
import json
import os
import sys

import yaml

from oceangraph.cli import (
    parse_args,
    setup_environment,
    validate_args,
    write_run_metadata,
)


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
    monkeypatch.delenv("OCEANGRAPH_COUNTERFACTUAL_VERIFICATION", raising=False)
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

    assert os.environ["DEEPSEEK_API_KEY"] == "test-key"
    assert "OCEANGRAPH_COUNTERFACTUAL_VERIFICATION" not in os.environ


def test_setup_environment_applies_explicit_strict_audit_options(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    _write_config(config_path)
    args = Namespace(
        config=str(config_path),
        api_key=None,
        backend="ollama",
        model=None,
        counterfactual_verification=True,
        multihop_verification_mode="strict",
        max_verification_chunks=6,
        max_unknown_verdicts=0,
        model_selection=True,
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

    assert os.environ["OCEANGRAPH_COUNTERFACTUAL_VERIFICATION"] == "1"
    assert os.environ["OCEANGRAPH_MULTIHOP_VERIFICATION_MODE"] == "strict"
    assert os.environ["OCEANGRAPH_MAX_VERIFICATION_CHUNKS"] == "6"
    assert os.environ["OCEANGRAPH_MAX_UNKNOWN_VERDICTS"] == "0"
    assert os.environ["OCEANGRAPH_MODEL_SELECTION"] == "1"


def test_run_metadata_records_four_agent_architecture(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "oceangraph",
            "--input",
            str(tmp_path),
            "--output",
            str(output_dir),
        ],
    )
    args = parse_args()

    write_run_metadata(args)

    metadata = json.loads(
        (output_dir / "oceangraph_run_config.json").read_text(encoding="utf-8")
    )
    assert metadata["framework_version"] == "3.0.0"
    assert metadata["agents"] == ["corpus", "evidence", "qa", "verifier"]
    assert metadata["agent_architecture"]["sequence"] == metadata["agents"]
