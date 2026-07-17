from oceangraph.verification import (
    evaluate_multihop_gate,
    parse_consolidated_multihop_response,
    prioritize_verification_chunks,
)


def test_counterfactual_gate_accepts_two_necessary_chunks():
    result = evaluate_multihop_gate(
        {"doc:a": "PARTIAL_ONLY", "doc:b": "PARTIAL_ONLY", "doc:c": "CANNOT_ANSWER"},
        {"doc:a": "PARTIAL_ONLY", "doc:b": "CANNOT_ANSWER", "doc:c": "CAN_ANSWER"},
        min_supporting_chunks=2,
    )

    assert result["passes"] is True
    assert result["necessary_chunks"] == ["doc:a", "doc:b"]
    assert result["redundant_chunks"] == ["doc:c"]


def test_counterfactual_gate_rejects_single_chunk_shortcut():
    result = evaluate_multihop_gate(
        {"doc:a": "CAN_ANSWER", "doc:b": "PARTIAL_ONLY"},
        {},
        min_supporting_chunks=2,
    )

    assert result["passes"] is False
    assert result["status"] == "SHORTCUT_FOUND"


def test_counterfactual_gate_rejects_redundant_evidence_set():
    result = evaluate_multihop_gate(
        {"doc:a": "PARTIAL_ONLY", "doc:b": "PARTIAL_ONLY"},
        {"doc:a": "CAN_ANSWER", "doc:b": "PARTIAL_ONLY"},
        min_supporting_chunks=2,
    )

    assert result["passes"] is False
    assert result["status"] == "INSUFFICIENT_NECESSARY_EVIDENCE"


def test_balanced_gate_allows_one_unknown_when_two_chunks_are_partial():
    result = evaluate_multihop_gate(
        {
            "doc:a": "PARTIAL_ONLY",
            "doc:b": "PARTIAL_ONLY",
            "doc:c": "UNKNOWN",
        },
        {},
        min_supporting_chunks=2,
        counterfactual_verification=False,
        max_unknown_chunks=1,
    )

    assert result["passes"] is True
    assert result["status"] == "MULTIHOP_REQUIRED_WITH_WARNINGS"


def test_evidence_references_are_prioritized_with_a_fixed_budget():
    labels = ["doc:a", "doc:b", "doc:c", "doc:d", "doc:e"]
    qa_pair = {
        "supporting_facts": [
            {"chunk": "Chunk 4", "fact": "bridge"},
            {"chunk": "Chunk 2", "fact": "answer"},
        ]
    }

    selected = prioritize_verification_chunks(
        labels,
        qa_pair,
        max_chunks=3,
        min_supporting_chunks=2,
    )

    assert selected == [3, 1, 0]


def test_consolidated_response_parser_fills_missing_checks_as_unknown():
    response = """{
      "single_chunk_checks": [
        {"chunk_index": 1, "status": "PARTIAL_ONLY", "explanation": "bridge"},
        {"chunk_index": 2, "status": "CANNOT_ANSWER", "explanation": "missing rule"}
      ]
    }"""

    statuses, checks = parse_consolidated_multihop_response(
        response,
        ["doc:a", "doc:b", "doc:c"],
    )

    assert statuses == {
        "doc:a": "PARTIAL_ONLY",
        "doc:b": "CANNOT_ANSWER",
        "doc:c": "UNKNOWN",
    }
    assert checks[2]["explanation"].startswith("No parseable")
