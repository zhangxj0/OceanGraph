from oceangraph.verification import evaluate_multihop_gate


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
