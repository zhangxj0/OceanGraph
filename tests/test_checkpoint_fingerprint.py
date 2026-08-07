import json

import pytest

from oceangraph.utils.checkpoint import (
    CheckpointManager,
    build_run_fingerprint,
    validate_output_fingerprint,
)


def test_run_fingerprint_ignores_target_but_changes_with_corpus_or_semantics(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    source = corpus / "ocean.txt"
    source.write_text("cold water sinks", encoding="utf-8")

    first, _ = build_run_fingerprint({"qa_generation": {"num_qa_pairs": 10}}, str(corpus))
    changed_config, _ = build_run_fingerprint(
        {"qa_generation": {"num_qa_pairs": 20}}, str(corpus)
    )
    changed_semantics, _ = build_run_fingerprint(
        {"qa_generation": {"num_qa_pairs": 10, "min_supporting_chunks": 3}},
        str(corpus),
    )
    source.write_text("warm water rises", encoding="utf-8")
    changed_corpus, _ = build_run_fingerprint(
        {"qa_generation": {"num_qa_pairs": 10}}, str(corpus)
    )

    assert first == changed_config
    assert first != changed_semantics
    assert first != changed_corpus


def test_run_fingerprint_includes_effective_runtime_and_model_routes(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "ocean.md").write_text("thermohaline circulation", encoding="utf-8")
    base, _ = build_run_fingerprint(
        {},
        str(corpus),
        runtime_settings={"retrieval": {"max_depth": 2}},
        model_routes={"generation": {"model": "Qwen"}},
    )
    changed_runtime, _ = build_run_fingerprint(
        {},
        str(corpus),
        runtime_settings={"retrieval": {"max_depth": 3}},
        model_routes={"generation": {"model": "Qwen"}},
    )
    changed_route, _ = build_run_fingerprint(
        {},
        str(corpus),
        runtime_settings={"retrieval": {"max_depth": 2}},
        model_routes={"generation": {"model": "Qwen-next"}},
    )

    assert base != changed_runtime
    assert base != changed_route


def test_run_fingerprint_ignores_execution_controls(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "ocean.md").write_text("ocean evidence", encoding="utf-8")
    first, _ = build_run_fingerprint(
        {"paths": {"output_dir": "first"}, "parallel": {"qa_max_workers": 1}},
        str(corpus),
        runtime_settings={
            "paths": {"output_dir": "first"},
            "parallel": {"qa_workers": 1},
            "qa_generation": {"target": 2, "min_supporting_chunks": 2},
        },
    )
    resumed, _ = build_run_fingerprint(
        {"paths": {"output_dir": "second"}, "parallel": {"qa_max_workers": 8}},
        str(corpus),
        runtime_settings={
            "paths": {"output_dir": "second"},
            "parallel": {"qa_workers": 8},
            "qa_generation": {"target": 80, "min_supporting_chunks": 2},
        },
    )

    assert first == resumed


def test_checkpoint_state_is_namespaced_by_fingerprint(tmp_path):
    first = CheckpointManager(str(tmp_path), run_fingerprint="a" * 64)
    second = CheckpointManager(str(tmp_path), run_fingerprint="b" * 64)

    first.mark_markdown_complete("doc", "doc.md")

    assert first.get_completed_markdown_files() == {"doc"}
    assert second.get_completed_markdown_files() == set()
    assert first.checkpoint_dir != second.checkpoint_dir


def test_output_manifest_rejects_mixed_runs(tmp_path):
    metadata = {"framework_version": "3.0.0", "config": {}, "sources": []}
    validate_output_fingerprint(str(tmp_path), "a" * 64, metadata)
    (tmp_path / "chunks.json").write_text("[]", encoding="utf-8")

    with pytest.raises(RuntimeError, match="different OceanGraph corpus"):
        validate_output_fingerprint(str(tmp_path), "b" * 64, metadata)

    manifest = json.loads(
        (tmp_path / "oceangraph_run_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["fingerprint"] == "a" * 64


def test_output_manifest_can_be_replaced_before_material_generation(tmp_path):
    metadata = {"framework_version": "3.0.0", "config": {}, "sources": []}
    validate_output_fingerprint(str(tmp_path), "a" * 64, metadata)

    validate_output_fingerprint(
        str(tmp_path),
        "b" * 64,
        metadata,
        write_manifest=False,
    )
    unchanged = json.loads(
        (tmp_path / "oceangraph_run_manifest.json").read_text(encoding="utf-8")
    )
    assert unchanged["fingerprint"] == "a" * 64

    validate_output_fingerprint(str(tmp_path), "b" * 64, metadata)
    replaced = json.loads(
        (tmp_path / "oceangraph_run_manifest.json").read_text(encoding="utf-8")
    )
    assert replaced["fingerprint"] == "b" * 64


def test_legacy_outputs_without_manifest_are_not_silently_reused(tmp_path):
    (tmp_path / "qa_multihop_pass.json").write_text("[]", encoding="utf-8")

    with pytest.raises(RuntimeError, match="no v3.0.0 fingerprint"):
        validate_output_fingerprint(
            str(tmp_path),
            "a" * 64,
            {"framework_version": "3.0.0", "config": {}, "sources": []},
        )
