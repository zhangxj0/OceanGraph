"""Pure decision logic for shortcut and counterfactual evidence checks."""

from __future__ import annotations

from typing import Any, Dict, Mapping


def evaluate_multihop_gate(
    single_chunk_statuses: Mapping[str, str],
    ablation_statuses: Mapping[str, str],
    *,
    min_supporting_chunks: int,
    counterfactual_verification: bool = True,
) -> Dict[str, Any]:
    """Combine model judgments into a deterministic multi-hop acceptance decision."""
    shortcut_chunks = [
        chunk for chunk, status in single_chunk_statuses.items() if status == "CAN_ANSWER"
    ]
    unknown_single = [
        chunk for chunk, status in single_chunk_statuses.items() if status == "UNKNOWN"
    ]
    partial_chunks = [
        chunk for chunk, status in single_chunk_statuses.items() if status == "PARTIAL_ONLY"
    ]
    necessary_chunks = [
        chunk
        for chunk, status in ablation_statuses.items()
        if status in {"PARTIAL_ONLY", "CANNOT_ANSWER"}
    ]
    redundant_chunks = [
        chunk for chunk, status in ablation_statuses.items() if status == "CAN_ANSWER"
    ]
    unknown_counterfactual = [
        chunk for chunk, status in ablation_statuses.items() if status == "UNKNOWN"
    ]

    if shortcut_chunks:
        status = "SHORTCUT_FOUND"
        passes = False
    elif unknown_single:
        status = "UNKNOWN_SINGLE_CHUNK_CHECK"
        passes = False
    elif counterfactual_verification and unknown_counterfactual:
        status = "UNKNOWN_COUNTERFACTUAL_CHECK"
        passes = False
    elif counterfactual_verification and len(necessary_chunks) < min_supporting_chunks:
        status = "INSUFFICIENT_NECESSARY_EVIDENCE"
        passes = False
    else:
        status = "MULTIHOP_REQUIRED"
        passes = len(partial_chunks) >= min_supporting_chunks

    return {
        "status": status,
        "passes": passes,
        "shortcut_chunks": shortcut_chunks,
        "unknown_single_chunks": unknown_single,
        "partial_chunks": partial_chunks,
        "necessary_chunks": necessary_chunks,
        "redundant_chunks": redundant_chunks,
        "unknown_counterfactual_chunks": unknown_counterfactual,
        "minimal_evidence_count": len(necessary_chunks),
    }
