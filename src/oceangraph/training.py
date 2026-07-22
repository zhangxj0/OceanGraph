"""Training-ready exports for verified OceanGraph multi-agent records."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

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


def to_training_record(
    item: Mapping[str, Any],
    *,
    split: str = "train",
    source_documents: Iterable[str] = (),
    split_group_id: str = "",
) -> Dict[str, Any]:
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
        "taxonomy_version": item.get("taxonomy_version", "3.0.0"),
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
            "architecture_version": "3.0.0",
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
            "source_documents": _unique_strings(source_documents),
            "split_group_id": split_group_id,
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


def _normalized_split_ratios(
    split_ratios: Mapping[str, float] | None,
) -> Dict[str, float]:
    configured = dict(split_ratios or {"train": 0.8, "dev": 0.1, "test": 0.1})
    ratios = {
        str(name).strip(): float(value)
        for name, value in configured.items()
        if str(name).strip() and float(value) > 0
    }
    total = sum(ratios.values())
    if not ratios or total <= 0:
        raise ValueError("training split ratios must contain at least one positive value")
    return {name: value / total for name, value in ratios.items()}


def _resolve_supporting_source_documents(
    item: Mapping[str, Any],
    chunk_sources: Mapping[str, str],
) -> tuple[List[str], List[str]]:
    """Resolve every supporting chunk against the exported retrieval corpus."""
    graph = item.get("evidence_graph") or {}
    sources = []
    unresolved = []
    for chunk_id in _unique_strings(graph.get("supporting_chunk_ids", []) or []):
        source = chunk_sources.get(chunk_id)
        if source:
            sources.append(source)
        else:
            unresolved.append(chunk_id)
    return _unique_strings(sources), _unique_strings(unresolved)


def _assign_document_group_splits(
    items: List[Mapping[str, Any]],
    source_sets: List[List[str]],
    split_ratios: Mapping[str, float],
    seed: int,
) -> List[tuple[str, str]]:
    """Assign connected source-document components to one deterministic split."""

    parent: Dict[str, str] = {}

    def find(value: str) -> str:
        parent.setdefault(value, value)
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[max(left_root, right_root)] = min(left_root, right_root)

    for sources in source_sets:
        for source in sources:
            find(source)
        for source in sources[1:]:
            union(sources[0], source)

    groups: Dict[str, List[int]] = defaultdict(list)
    for index, (item, sources) in enumerate(zip(items, source_sets)):
        if sources:
            group_key = find(sources[0])
        else:
            group_key = f"qa:{item.get('qa_id') or stable_qa_id(item)}"
        groups[group_key].append(index)

    ordered_groups = sorted(
        groups.items(),
        key=lambda pair: hashlib.sha256(
            f"{int(seed)}:{pair[0]}".encode("utf-8")
        ).hexdigest(),
    )
    total_records = len(items)
    target_counts = {
        name: ratio * total_records for name, ratio in split_ratios.items()
    }
    assigned_counts = {name: 0 for name in split_ratios}
    assignments: List[tuple[str, str] | None] = [None] * total_records

    for group_key, indices in ordered_groups:
        split_name = max(
            split_ratios,
            key=lambda name: (
                target_counts[name] - assigned_counts[name],
                split_ratios[name],
                name == "train",
                name,
            ),
        )
        group_id = "source_group_" + hashlib.sha256(
            group_key.encode("utf-8")
        ).hexdigest()[:16]
        for index in indices:
            assignments[index] = (split_name, group_id)
        assigned_counts[split_name] += len(indices)

    if any(assignment is None for assignment in assignments):
        raise RuntimeError("failed to assign every accepted QA record to a split")
    return [assignment for assignment in assignments if assignment is not None]


def export_training_dataset(
    qa_pairs: Iterable[Mapping[str, Any]],
    chunks: Iterable[Mapping[str, Any]],
    output_dir: str | Path,
    *,
    split: str | None = None,
    split_ratios: Mapping[str, float] | None = None,
    split_seed: int = 42,
) -> Dict[str, Any]:
    """Export verified QA with source-document-disjoint dataset splits.

    Passing ``split`` retains the legacy single-file export.  Otherwise, all
    documents linked by any QA evidence graph are kept in one connected group
    and assigned deterministically according to ``split_ratios``.
    """
    output_path = Path(output_dir)
    accepted_items: List[Mapping[str, Any]] = []
    rejected_reasons: Counter[str] = Counter()
    total = 0
    for item in qa_pairs:
        total += 1
        reasons = validate_training_record(item)
        if reasons:
            rejected_reasons.update(reasons)
            continue
        accepted_items.append(item)

    corpus = to_corpus_records(chunks)
    chunk_sources = {
        str(record["id"]): str(record.get("file_name", ""))
        for record in corpus
    }
    resolved_items: List[Mapping[str, Any]] = []
    source_sets: List[List[str]] = []
    unresolved_supporting_ids: List[str] = []
    unresolved_record_count = 0
    for item in accepted_items:
        sources, unresolved = _resolve_supporting_source_documents(item, chunk_sources)
        if unresolved:
            unresolved_record_count += 1
            unresolved_supporting_ids.extend(unresolved)
            rejected_reasons.update(["unresolved_supporting_chunks"])
            continue
        resolved_items.append(item)
        source_sets.append(sources)
    accepted_items = resolved_items

    if split is not None:
        split_names = [str(split)]
        assignments = [(str(split), "single_split") for _ in accepted_items]
        normalized_ratios = {str(split): 1.0}
    else:
        normalized_ratios = _normalized_split_ratios(split_ratios)
        split_names = list(normalized_ratios)
        assignments = _assign_document_group_splits(
            accepted_items,
            source_sets,
            normalized_ratios,
            split_seed,
        )

    rows_by_split: Dict[str, List[Dict[str, Any]]] = {
        name: [] for name in split_names
    }
    sources_by_split: Dict[str, set[str]] = {name: set() for name in split_names}
    for item, sources, (split_name, group_id) in zip(
        accepted_items, source_sets, assignments
    ):
        rows_by_split[split_name].append(
            to_training_record(
                item,
                split=split_name,
                source_documents=sources,
                split_group_id=group_id,
            )
        )
        sources_by_split[split_name].update(sources)

    qa_files = {}
    for split_name, records in rows_by_split.items():
        qa_path = output_path / f"{split_name}.jsonl"
        _write_jsonl(qa_path, records)
        qa_files[split_name] = qa_path.name

    corpus_path = output_path / "corpus.jsonl"
    _write_jsonl(corpus_path, corpus)
    source_overlaps = {
        f"{left}:{right}": sorted(sources_by_split[left] & sources_by_split[right])
        for index, left in enumerate(split_names)
        for right in split_names[index + 1 :]
    }
    component_sizes = Counter(group_id for _, group_id in assignments)
    largest_component_records = max(component_sizes.values(), default=0)
    empty_splits = [
        name for name, records in rows_by_split.items() if not records
    ]
    source_leakage_detected = any(source_overlaps.values())
    split_viable = bool(accepted_items) and not empty_splits and not source_leakage_detected
    manifest = {
        "schema_version": TRAINING_SCHEMA_VERSION,
        "split": split,
        "split_strategy": "single" if split is not None else "source_document_components",
        "split_seed": int(split_seed),
        "split_ratios": normalized_ratios,
        "split_counts": {
            name: len(records) for name, records in rows_by_split.items()
        },
        "split_files": qa_files,
        "source_documents_per_split": {
            name: len(sources) for name, sources in sources_by_split.items()
        },
        "source_document_overlaps": source_overlaps,
        "source_leakage_detected": source_leakage_detected,
        "split_viable": split_viable,
        "empty_splits": empty_splits,
        "source_component_count": len(component_sizes),
        "largest_component_records": largest_component_records,
        "largest_component_fraction": (
            largest_component_records / len(accepted_items) if accepted_items else 0.0
        ),
        "unresolved_supporting_chunk_records": unresolved_record_count,
        "unresolved_supporting_chunk_ids": sorted(
            set(unresolved_supporting_ids)
        )[:100],
        "input_records": total,
        "exported_records": len(accepted_items),
        "rejected_records": total - len(accepted_items),
        "rejection_reasons": dict(sorted(rejected_reasons.items())),
        "corpus_records": len(corpus),
        "qa_file": qa_files.get(str(split)) if split is not None else None,
        "corpus_file": corpus_path.name,
    }
    manifest_path = output_path / "manifest.json"
    manifest_temp = manifest_path.with_suffix(".json.tmp")
    manifest_temp.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    manifest_temp.replace(manifest_path)
    return manifest


__all__ = [
    "TRAINING_SCHEMA_VERSION",
    "export_training_dataset",
    "stable_qa_id",
    "to_corpus_records",
    "to_training_record",
    "validate_training_record",
]
