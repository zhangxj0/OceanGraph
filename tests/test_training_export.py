import json

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
