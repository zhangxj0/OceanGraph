import json

import pytest

from oceangraph.utils.checkpoint import (
    CheckpointManager,
    build_run_fingerprint,
    validate_output_fingerprint,
)


def test_run_fingerprint_changes_with_corpus_or_config(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    source = corpus / "ocean.txt"
    source.write_text("cold water sinks", encoding="utf-8")

    first, _ = build_run_fingerprint({"qa_generation": {"num_qa_pairs": 10}}, str(corpus))
    changed_config, _ = build_run_fingerprint(
        {"qa_generation": {"num_qa_pairs": 20}}, str(corpus)
    )
    source.write_text("warm water rises", encoding="utf-8")
    changed_corpus, _ = build_run_fingerprint(
        {"qa_generation": {"num_qa_pairs": 10}}, str(corpus)
    )

    assert first != changed_config
    assert first != changed_corpus


def test_checkpoint_state_is_namespaced_by_fingerprint(tmp_path):
    first = CheckpointManager(str(tmp_path), run_fingerprint="a" * 64)
    second = CheckpointManager(str(tmp_path), run_fingerprint="b" * 64)

    first.mark_markdown_complete("doc", "doc.md")

    assert first.get_completed_markdown_files() == {"doc"}
    assert second.get_completed_markdown_files() == set()
    assert first.checkpoint_dir != second.checkpoint_dir


def test_output_manifest_rejects_mixed_runs(tmp_path):
    metadata = {"framework_version": "2.2.1", "config": {}, "sources": []}
    validate_output_fingerprint(str(tmp_path), "a" * 64, metadata)
    (tmp_path / "chunks.json").write_text("[]", encoding="utf-8")

    with pytest.raises(RuntimeError, match="different OceanGraph corpus"):
        validate_output_fingerprint(str(tmp_path), "b" * 64, metadata)

    manifest = json.loads(
        (tmp_path / "oceangraph_run_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["fingerprint"] == "a" * 64


def test_legacy_outputs_without_manifest_are_not_silently_reused(tmp_path):
    (tmp_path / "qa_multihop_pass.json").write_text("[]", encoding="utf-8")

    with pytest.raises(RuntimeError, match="no v2.2.1 fingerprint"):
        validate_output_fingerprint(
            str(tmp_path),
            "a" * 64,
            {"framework_version": "2.2.1", "config": {}, "sources": []},
        )
