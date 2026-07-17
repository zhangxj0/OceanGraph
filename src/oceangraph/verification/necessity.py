"""Pure decision logic for shortcut and counterfactual evidence checks."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple


VALID_CHUNK_STATUSES = {"CAN_ANSWER", "PARTIAL_ONLY", "CANNOT_ANSWER", "UNKNOWN"}


def evaluate_multihop_gate(
    single_chunk_statuses: Mapping[str, str],
    ablation_statuses: Mapping[str, str],
    *,
    min_supporting_chunks: int,
    counterfactual_verification: bool = True,
    max_unknown_chunks: int = 0,
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
    elif len(unknown_single) > max_unknown_chunks:
        status = "UNKNOWN_SINGLE_CHUNK_CHECK"
        passes = False
    elif counterfactual_verification and unknown_counterfactual:
        status = "UNKNOWN_COUNTERFACTUAL_CHECK"
        passes = False
    elif counterfactual_verification and len(necessary_chunks) < min_supporting_chunks:
        status = "INSUFFICIENT_NECESSARY_EVIDENCE"
        passes = False
    else:
        passes = len(partial_chunks) >= min_supporting_chunks
        status = (
            "MULTIHOP_REQUIRED_WITH_WARNINGS"
            if passes and unknown_single
            else "MULTIHOP_REQUIRED"
        )

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
        "max_unknown_chunks": max_unknown_chunks,
    }


def prioritize_verification_chunks(
    chunk_labels: Sequence[str],
    qa_pair: Mapping[str, Any] | None,
    *,
    max_chunks: int,
    min_supporting_chunks: int,
) -> List[int]:
    """Choose evidence-linked chunks first, then fill deterministically."""
    if not chunk_labels:
        return []

    limit = min(len(chunk_labels), max(max_chunks, min_supporting_chunks))
    selected: List[int] = []
    references: List[str] = []
    qa_pair = qa_pair or {}
    for field_name in ("supporting_facts", "evidence_spans"):
        for item in qa_pair.get(field_name, []) or []:
            if isinstance(item, Mapping):
                reference = str(item.get("chunk", "")).strip()
                if reference:
                    references.append(reference)

    for reference in references:
        numeric_match = re.search(r"\bchunk[\s_:#-]*(\d+)\b", reference, re.IGNORECASE)
        if numeric_match:
            index = int(numeric_match.group(1)) - 1
            if 0 <= index < len(chunk_labels) and index not in selected:
                selected.append(index)
        reference_key = reference.casefold()
        for index, label in enumerate(chunk_labels):
            if reference_key and reference_key in label.casefold() and index not in selected:
                selected.append(index)

    for index in range(len(chunk_labels)):
        if index not in selected:
            selected.append(index)
        if len(selected) >= limit:
            break
    return selected[:limit]


def parse_consolidated_multihop_response(
    response: str,
    chunk_labels: Sequence[str],
) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Parse one model response containing independent judgments for many chunks."""
    payload = _extract_json_payload(response)
    raw_checks = payload.get("single_chunk_checks") or payload.get("checks") or []
    parsed_by_label: Dict[str, Dict[str, str]] = {}

    for raw_check in raw_checks:
        if not isinstance(raw_check, Mapping):
            continue
        label = _resolve_check_label(raw_check, chunk_labels)
        if not label:
            continue
        status = str(raw_check.get("status", "UNKNOWN")).strip().upper()
        if status not in VALID_CHUNK_STATUSES:
            status = "UNKNOWN"
        parsed_by_label[label] = {
            "chunk": label,
            "status": status,
            "explanation": str(raw_check.get("explanation", "")).strip(),
        }

    checks = []
    statuses = {}
    for label in chunk_labels:
        check = parsed_by_label.get(label) or {
            "chunk": label,
            "status": "UNKNOWN",
            "explanation": "No parseable judgment returned for this chunk.",
        }
        checks.append(check)
        statuses[label] = check["status"]
    return statuses, checks


def _extract_json_payload(response: str) -> Dict[str, Any]:
    if not response:
        return {}
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = response.find("{")
        end = response.rfind("}")
        if start < 0 or end <= start:
            return {}
        candidate = response[start:end + 1]
    try:
        payload = json.loads(candidate)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        return {}


def _resolve_check_label(
    raw_check: Mapping[str, Any],
    chunk_labels: Sequence[str],
) -> str:
    try:
        index = int(raw_check.get("chunk_index", 0)) - 1
    except (TypeError, ValueError):
        index = -1
    if 0 <= index < len(chunk_labels):
        return chunk_labels[index]

    requested = str(raw_check.get("chunk", "")).strip().casefold()
    for label in chunk_labels:
        if requested == label.casefold():
            return label
    return ""
