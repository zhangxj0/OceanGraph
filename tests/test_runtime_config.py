import os
import sys
import types

import yaml

from oceangraph import OceanGraph, OceanGraphConfig
from oceangraph.core.config import clear_runtime_config, load_config, set_runtime_config
from oceangraph.core.llm import reset_llm_runtime


def test_runtime_config_maps_public_execution_fields(tmp_path):
    base_path = tmp_path / "base.yaml"
    base_path.write_text(
        yaml.safe_dump(
            {
                "models": {"profiles": {"verifier": {"backend": "OPENAI"}}},
                "retrieval": {"multihop": {"max_breadth": 2}},
            }
        ),
        encoding="utf-8",
    )
    config = OceanGraphConfig(
        config_file=str(base_path),
        max_breadth=7,
        chunk_window_size=12000,
        chunk_overlap_size=1200,
        multihop_verification_mode="strict",
        verification_profile="cost_efficient",
        max_answer_words=7,
        max_answer_cjk_chars=14,
        counterfactual_verification=True,
        enable_checkpointing=False,
        export_training_data=True,
        training_split="train",
    )

    runtime = config.to_runtime_config()

    assert runtime["models"]["profiles"]["verifier"]["backend"] == "OPENAI"
    assert runtime["retrieval"]["multihop"]["max_breadth"] == 7
    assert runtime["chunking"] == {"window_size": 12000, "overlap_size": 1200}
    assert runtime["qa_generation"]["multihop_verification_mode"] == "strict"
    assert runtime["qa_generation"]["verification_profile"] == "cost_efficient"
    assert runtime["qa_generation"]["max_answer_words"] == 7
    assert runtime["qa_generation"]["max_answer_cjk_chars"] == 14
    assert runtime["qa_generation"]["counterfactual_verification"] is True
    assert runtime["checkpointing"]["enabled"] is False
    assert runtime["training_export"] == {"enabled": True, "split": "train"}


def test_yaml_round_trip_preserves_new_runtime_controls(tmp_path):
    path = tmp_path / "saved.yaml"
    original = OceanGraphConfig(
        max_breadth=8,
        chunk_window_size=9000,
        chunk_overlap_size=900,
        model_selection=True,
        verification_profile="cost_efficient",
        max_answer_words=6,
        max_answer_cjk_chars=12,
        max_verification_chunks=6,
        max_unknown_verdicts=0,
        run_deduplication=True,
        enable_checkpointing=False,
        export_training_data=False,
        training_split="validation",
    )

    original.save_yaml(str(path))
    loaded = OceanGraphConfig.from_yaml(str(path))

    assert loaded.max_breadth == 8
    assert loaded.chunk_window_size == 9000
    assert loaded.chunk_overlap_size == 900
    assert loaded.model_selection is True
    assert loaded.verification_profile == "cost_efficient"
    assert loaded.max_answer_words == 6
    assert loaded.max_answer_cjk_chars == 12
    assert loaded.max_verification_chunks == 6
    assert loaded.max_unknown_verdicts == 0
    assert loaded.run_deduplication is True
    assert loaded.enable_checkpointing is False
    assert loaded.export_training_data is False
    assert loaded.training_split == "validation"


def test_setup_environment_writes_false_flags_over_stale_values(monkeypatch, tmp_path):
    for name in (
        "OCEANGRAPH_RUN_DEDUPLICATION",
        "OCEANGRAPH_RUN_EVALUATION",
        "OCEANGRAPH_MODEL_SELECTION",
        "OCEANGRAPH_COUNTERFACTUAL_VERIFICATION",
        "OCEANGRAPH_ENABLE_CHECKPOINTING",
    ):
        monkeypatch.setenv(name, "1")

    pipeline = OceanGraph(
        output_dir=str(tmp_path),
        run_deduplication=False,
        run_evaluation=False,
        model_selection=False,
        counterfactual_verification=False,
        enable_checkpointing=False,
    )
    try:
        pipeline._setup_environment()
        assert os.environ["OCEANGRAPH_RUN_DEDUPLICATION"] == "0"
        assert os.environ["OCEANGRAPH_RUN_EVALUATION"] == "0"
        assert os.environ["OCEANGRAPH_MODEL_SELECTION"] == "0"
        assert os.environ["OCEANGRAPH_COUNTERFACTUAL_VERIFICATION"] == "0"
        assert os.environ["OCEANGRAPH_ENABLE_CHECKPOINTING"] == "0"
        assert load_config()["checkpointing"]["enabled"] is False
    finally:
        clear_runtime_config()
        reset_llm_runtime(reset_tokens=True)


def test_run_restores_environment_and_clears_runtime_config(monkeypatch, tmp_path):
    observed = {}
    fake_engine = types.ModuleType("oceangraph.engine")

    def fake_run_pipeline(config):
        observed["backend"] = os.environ["OCEANGRAPH_BACKEND"]
        observed["output_dir"] = load_config()["paths"]["output_dir"]
        observed["config"] = config

    fake_engine.run_pipeline = fake_run_pipeline
    monkeypatch.setitem(sys.modules, "oceangraph.engine", fake_engine)
    monkeypatch.setenv("OCEANGRAPH_BACKEND", "LEGACY")
    monkeypatch.setenv("OCEANGRAPH_RUN_DEDUPLICATION", "1")

    pipeline = OceanGraph(
        backend="ollama",
        output_dir=str(tmp_path / "result"),
        run_deduplication=False,
    )
    results = pipeline.run()

    assert observed["backend"] == "OLLAMA"
    assert observed["output_dir"] == str(tmp_path / "result")
    assert observed["config"] is pipeline.config
    assert os.environ["OCEANGRAPH_BACKEND"] == "LEGACY"
    assert os.environ["OCEANGRAPH_RUN_DEDUPLICATION"] == "1"
    assert results.output_dir == str(tmp_path / "result")


def test_deduplication_thresholds_refresh_between_runs():
    from oceangraph.pipeline import deduplication

    try:
        set_runtime_config(
            {
                "deduplication": {
                    "alpha": 0.25,
                    "question_similarity_threshold": 0.82,
                    "answer_similarity": {"low": 0.66},
                }
            }
        )
        deduplication.refresh_deduplication_config()

        assert deduplication.ALPHA == 0.25
        assert deduplication.QUESTION_SIMILARITY_THRESHOLD == 0.82
        assert deduplication.ANSWER_SIMILARITY_LOW == 0.66
    finally:
        clear_runtime_config()
