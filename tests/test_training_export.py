import json
from copy import deepcopy

from oceangraph import OceanGraphResults
from oceangraph.training import (
    export_training_dataset,
    stable_qa_id,
    validate_training_record,
)


def _valid_record():
    return {
        "question": "Which process transports particulate carbon to depth?",
        "answer": "biological pump",
        "short_answers": ["biological pump"],
        "answer_type": "entity",
        "domain": "Ocean Carbon Cycle and Marine Biogeochemistry",
        "subdomain": "carbon_biogeochemistry",
        "hop_count": 2,
        "supporting_facts": [
            {"chunk": "Chunk 1", "fact": "Particles contain carbon."},
            {"chunk": "Chunk 2", "fact": "The pump exports particles."},
        ],
        "evidence_graph": {
            "supporting_chunk_ids": ["carbon:1", "biology:2"],
            "nodes": [],
            "edges": [],
        },
        "multihop_necessity_result": {
            "passes": True,
            "status": "MULTIHOP_REQUIRED",
            "verification_mode": "balanced",
        },
        "agent_trace": [
            {"agent_id": "corpus", "status": "completed"},
            {"agent_id": "evidence", "status": "completed"},
            {"agent_id": "qa", "status": "completed"},
            {"agent_id": "verifier", "status": "accepted"},
        ],
        "coordination_trace": {"status": "accepted"},
    }


def test_training_validation_requires_verified_evidence_and_all_agents():
    record = _valid_record()
    assert validate_training_record(record) == []

    record["hop_count"] = 3
    record["agent_trace"] = record["agent_trace"][:-1]
    reasons = validate_training_record(record)

    assert "hop_count_mismatch" in reasons
    assert "incomplete_agent_trace" in reasons


def test_training_validation_rejects_open_ended_answer_type():
    record = _valid_record()
    record["answer_type"] = "list"

    assert "unsupported_answer_type" in validate_training_record(record)


def test_training_export_is_compact_and_uses_aligned_corpus_ids(tmp_path):
    record = _valid_record()
    chunks = [
        {"file_name": "carbon", "chunk_id": "1", "content": "Particles contain carbon."},
        {"file_name": "biology", "chunk_id": "2", "content": "The pump exports particles."},
    ]

    manifest = export_training_dataset([record], chunks, tmp_path, split="train")
    training_row = json.loads((tmp_path / "train.jsonl").read_text(encoding="utf-8"))
    corpus_rows = [
        json.loads(line)
        for line in (tmp_path / "corpus.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert manifest["exported_records"] == 1
    assert manifest["split_viable"] is True
    assert training_row["qa_id"] == stable_qa_id(record)
    assert "context_chunks" not in training_row
    assert [row["id"] for row in corpus_rows] == ["carbon:1", "biology:2"]


def test_results_api_exports_training_dataset(tmp_path):
    results = OceanGraphResults(
        qa_pairs=[_valid_record()],
        chunks=[
            {"file_name": "carbon", "chunk_id": "1", "content": "Particles contain carbon."},
            {"file_name": "biology", "chunk_id": "2", "content": "The pump exports particles."},
        ],
    )

    manifest = results.export_training(str(tmp_path / "training"))

    assert manifest["exported_records"] == 1
    assert (tmp_path / "training" / "manifest.json").exists()
    assert (tmp_path / "training" / "train.jsonl").exists()


def test_training_splits_keep_connected_source_documents_together(tmp_path):
    records = []
    chunks = []
    for index in range(12):
        left = f"source_{index}_a"
        right = f"source_{index}_b"
        record = deepcopy(_valid_record())
        record["question"] = f"Which process is identified for ocean sample {index}?"
        record["answer"] = f"process {index}"
        record["short_answers"] = [f"process {index}"]
        record["evidence_graph"]["supporting_chunk_ids"] = [
            f"{left}:1",
            f"{right}:1",
        ]
        records.append(record)
        chunks.extend(
            [
                {"file_name": left, "chunk_id": "1", "content": f"Evidence {index}a"},
                {"file_name": right, "chunk_id": "1", "content": f"Evidence {index}b"},
            ]
        )

    first = export_training_dataset(records, chunks, tmp_path / "first", split_seed=9)
    second = export_training_dataset(records, chunks, tmp_path / "second", split_seed=9)

    assert first["source_leakage_detected"] is False
    assert first["split_viable"] is True
    assert first["empty_splits"] == []
    assert first["split_counts"] == second["split_counts"]
    assert sum(first["split_counts"].values()) == 12
    assert set(first["split_files"]) == {"train", "dev", "test"}

    assignments = {}
    for split_name, file_name in first["split_files"].items():
        for line in (tmp_path / "first" / file_name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            assignments[row["qa_id"]] = split_name
            assert row["metadata"]["source_documents"]

    repeated_assignments = {}
    for split_name, file_name in second["split_files"].items():
        for line in (tmp_path / "second" / file_name).read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            repeated_assignments[row["qa_id"]] = split_name

    assert assignments == repeated_assignments


def test_training_manifest_flags_one_giant_source_component(tmp_path):
    records = []
    chunks = [
        {"file_name": "shared", "chunk_id": "1", "content": "Shared evidence."},
        {"file_name": "bridge", "chunk_id": "1", "content": "Bridge evidence."},
    ]
    for index in range(10):
        record = deepcopy(_valid_record())
        record["question"] = f"Which process is shared by sample {index}?"
        record["answer"] = f"process {index}"
        record["short_answers"] = [f"process {index}"]
        record["evidence_graph"]["supporting_chunk_ids"] = ["shared:1", "bridge:1"]
        records.append(record)

    manifest = export_training_dataset(records, chunks, tmp_path)

    assert manifest["split_viable"] is False
    assert manifest["empty_splits"] == ["dev", "test"]
    assert manifest["source_component_count"] == 1
    assert manifest["largest_component_fraction"] == 1.0


def test_training_export_rejects_unresolved_supporting_chunks(tmp_path):
    record = _valid_record()
    chunks = [
        {"file_name": "carbon", "chunk_id": "1", "content": "Carbon evidence."},
    ]

    manifest = export_training_dataset([record], chunks, tmp_path, split="train")

    assert manifest["exported_records"] == 0
    assert manifest["rejected_records"] == 1
    assert manifest["rejection_reasons"]["unresolved_supporting_chunks"] == 1
    assert manifest["unresolved_supporting_chunk_records"] == 1
    assert manifest["unresolved_supporting_chunk_ids"] == ["biology:2"]
