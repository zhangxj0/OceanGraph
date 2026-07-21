import torch

from oceangraph.pipeline.deduplication import process_cluster_by_similarity


def test_deduplication_selects_one_verified_record_without_rewriting():
    first = {
        "question": "Which process links observations A and B?",
        "answer": "Process C.",
        "relevance_score": "8",
        "difficulty_score": "7",
        "supporting_facts": [{"chunk": "Chunk 1", "fact": "A"}],
        "evidence_spans": [{"chunk": "Chunk 1", "span": "A"}],
        "verification_result": "accepted-first",
    }
    second = {
        "question": "What connects observations A and B?",
        "answer": "Process C.",
        "relevance_score": "9",
        "difficulty_score": "8",
        "supporting_facts": [{"chunk": "Chunk 2", "fact": "B"}],
        "evidence_spans": [{"chunk": "Chunk 2", "span": "B"}],
        "verification_result": "accepted-second",
    }

    result = process_cluster_by_similarity(
        [first, second],
        [0, 1],
        torch.tensor([[1.0, 0.0], [0.99, 0.01]]),
        llm_merger=None,
        expert_persona="Ocean scientist",
        domain="Ocean science",
    )

    assert len(result) == 1
    selected = result[0]
    assert selected["question"] == second["question"]
    assert selected["answer"] == second["answer"]
    assert selected["supporting_facts"] == second["supporting_facts"]
    assert selected["evidence_spans"] == second["evidence_spans"]
    assert selected["verification_result"] == "accepted-second"
    assert selected["dedup_method"] == "select_verified_record"
    assert selected["dedup_preserved_verification"] is True
    assert "reorganized" not in selected


def test_safe_deduplication_does_not_mutate_source_record():
    record = {
        "question": "Question?",
        "answer": "Answer.",
        "relevance_score": 1,
        "difficulty_score": 1,
    }
    duplicate = dict(record)

    process_cluster_by_similarity(
        [record, duplicate],
        [0, 1],
        torch.eye(2),
        llm_merger=None,
        expert_persona="Ocean scientist",
        domain="Ocean science",
    )

    assert "dedup_method" not in record
    assert "dedup_method" not in duplicate
