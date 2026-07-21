"""Training-ready exports for verified OceanGraph multi-agent records."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

from oceangraph.pipeline.evidence_graph import stable_chunk_id
from oceangraph.pipeline.taxonomy import normalize_answer_type
from oceangraph.verification.quality import atomic_qa_violations


TRAINING_SCHEMA_VERSION = "oceangraph.training.v1"
REQUIRED_AGENTS = {"corpus", "evidence", "qa", "verifier"}


def _unique_strings(values: Iterable[Any]) -> List[str]:
    if isinstance(values, (str, bytes)):
        values = [values]
    output: List[str] = []
    seen = set()
    for value in values:
        cleaned = " ".join(str(value or "").split()).strip(" .;,")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def validate_training_record(item: Mapping[str, Any]) -> List[str]:
    """Return deterministic rejection reasons for unsafe training samples."""
    reasons: List[str] = []
    if not str(item.get("question", "")).strip():
        reasons.append("missing_question")
    if not str(item.get("answer", "")).strip():
        reasons.append("missing_answer")
    if not _unique_strings(item.get("short_answers", []) or []):
        reasons.append("missing_short_answers")
    if not normalize_answer_type(item.get("answer_type", "")):
        reasons.append("unsupported_answer_type")
    for violation in atomic_qa_violations(
        str(item.get("question", "")),
        str(item.get("answer", "")),
        item.get("short_answers", []) or [],
    ):
        reasons.append(f"qa_quality:{violation}")

    necessity = item.get("multihop_necessity_result") or {}
    if necessity.get("passes") is not True:
        reasons.append("multihop_not_verified")

    graph = item.get("evidence_graph") or {}
    supporting_ids = _unique_strings(graph.get("supporting_chunk_ids", []) or [])
    if len(supporting_ids) < 2:
        reasons.append("insufficient_grounded_evidence")
    try:
        hop_count = int(item.get("hop_count", 0) or 0)
    except (TypeError, ValueError):
        hop_count = 0
    if hop_count != len(supporting_ids):
        reasons.append("hop_count_mismatch")

    trace_agents = {
        str(event.get("agent_id", "")).strip().casefold()
        for event in item.get("agent_trace", []) or []
        if isinstance(event, Mapping)
    }
    if not REQUIRED_AGENTS.issubset(trace_agents):
        reasons.append("incomplete_agent_trace")
    verifier_accepted = any(
        str(event.get("agent_id", "")).strip().casefold() == "verifier"
        and str(event.get("status", "")).strip().casefold() == "accepted"
        for event in item.get("agent_trace", []) or []
        if isinstance(event, Mapping)
    )
    if not verifier_accepted:
        reasons.append("verifier_not_accepted")
    if str((item.get("coordination_trace") or {}).get("status", "")).casefold() != "accepted":
        reasons.append("coordinator_not_accepted")
    return reasons


def stable_qa_id(item: Mapping[str, Any]) -> str:
    graph = item.get("evidence_graph") or {}
    identity = {
        "question": " ".join(str(item.get("question", "")).split()),
        "answer": " ".join(str(item.get("answer", "")).split()),
        "supporting_chunk_ids": _unique_strings(
            graph.get("supporting_chunk_ids", []) or []
        ),
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:20]
    return f"oceangraph_{digest}"


def to_training_record(item: Mapping[str, Any], *, split: str = "train") -> Dict[str, Any]:
    """Normalize one accepted QA item without duplicating full context text."""
    graph = dict(item.get("evidence_graph") or {})
    necessity = dict(item.get("multihop_necessity_result") or {})
    question = " ".join(str(item.get("question", "")).split())
    answer = " ".join(str(item.get("answer", "")).split())
    return {
        "schema_version": TRAINING_SCHEMA_VERSION,
        "qa_id": str(item.get("qa_id") or stable_qa_id(item)),
        "split": split,
        "messages": [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ],
        "question": question,
        "answer": answer,
        "short_answers": _unique_strings(item.get("short_answers", []) or []),
        "domain": item.get("domain", ""),
        "subdomain": item.get("subdomain", ""),
        "taxonomy_version": item.get("taxonomy_version", "2.2.1"),
        "question_type": item.get("question_type", ""),
        "answer_type": normalize_answer_type(item.get("answer_type", "")),
        "hop_count": int(item.get("hop_count", 0) or 0),
        "reasoning": {
            "sub_questions": list(item.get("sub_questions", []) or []),
            "reasoning_path": item.get("reasoning_path", ""),
        },
        "evidence": {
            "supporting_chunk_ids": list(graph.get("supporting_chunk_ids", []) or []),
            "supporting_facts": list(item.get("supporting_facts", []) or []),
            "evidence_spans": list(item.get("evidence_spans", []) or []),
            "graph": graph,
        },
        "retrieval": {
            "search_history": list(item.get("search_history", []) or []),
            "search_trajectory": list(item.get("search_trajectory", []) or []),
            "retrieval_hop_count": int(item.get("retrieval_hop_count", 0) or 0),
        },
        "multi_agent": {
            "architecture_version": "2.2.1",
            "agent_trace": list(item.get("agent_trace", []) or []),
            "coordination_trace": dict(item.get("coordination_trace") or {}),
        },
        "verification": {
            "passes": necessity.get("passes") is True,
            "status": necessity.get("status", ""),
            "mode": necessity.get("verification_mode", ""),
            "profile": necessity.get("verification_profile", ""),
            "api_calls": int(necessity.get("verification_api_calls", 0) or 0),
        },
        "metadata": {
            "source_chunk_id": item.get("chunk_id"),
            "relevance_score": item.get("relevance_score", 0),
            "difficulty_score": item.get("difficulty_score", 0),
            "selection_status": item.get("selection_status", ""),
        },
    }


def to_corpus_records(chunks: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    records = []
    seen = set()
    for index, chunk in enumerate(chunks, 1):
        content = str(chunk.get("content", "")).strip()
        if not content:
            continue
        chunk_id = stable_chunk_id(dict(chunk), index)
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        records.append(
            {
                "id": chunk_id,
                "contents": content,
                "file_name": chunk.get("file_name", ""),
                "source_chunk_id": chunk.get("chunk_id", ""),
            }
        )
    return records


def _write_jsonl(path: Path, records: Iterable[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    temp_path.replace(path)


def export_training_dataset(
    qa_pairs: Iterable[Mapping[str, Any]],
    chunks: Iterable[Mapping[str, Any]],
    output_dir: str | Path,
    *,
    split: str = "train",
) -> Dict[str, Any]:
    """Export compact verified QA, aligned corpus, and a rejection manifest."""
    output_path = Path(output_dir)
    accepted: List[Dict[str, Any]] = []
    rejected_reasons: Counter[str] = Counter()
    total = 0
    for item in qa_pairs:
        total += 1
        reasons = validate_training_record(item)
        if reasons:
            rejected_reasons.update(reasons)
            continue
        accepted.append(to_training_record(item, split=split))

    corpus = to_corpus_records(chunks)
    qa_path = output_path / f"{split}.jsonl"
    corpus_path = output_path / "corpus.jsonl"
    _write_jsonl(qa_path, accepted)
    _write_jsonl(corpus_path, corpus)
    manifest = {
        "schema_version": TRAINING_SCHEMA_VERSION,
        "split": split,
        "input_records": total,
        "exported_records": len(accepted),
        "rejected_records": total - len(accepted),
        "rejection_reasons": dict(sorted(rejected_reasons.items())),
        "corpus_records": len(corpus),
        "qa_file": qa_path.name,
        "corpus_file": corpus_path.name,
    }
    (output_path / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


__all__ = [
    "TRAINING_SCHEMA_VERSION",
    "export_training_dataset",
    "stable_qa_id",
    "to_corpus_records",
    "to_training_record",
    "validate_training_record",
]
