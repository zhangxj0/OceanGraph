"""Evidence graph and reward-target utilities for generated multi-hop QA."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Dict, List


STOPWORDS = {
    "about", "above", "after", "again", "against", "along", "also", "among",
    "because", "before", "being", "below", "between", "could", "during", "each",
    "from", "have", "into", "more", "only", "other", "over", "same", "some",
    "such", "than", "that", "their", "then", "there", "these", "this", "those",
    "through", "under", "using", "when", "where", "which", "while", "with",
    "within", "without", "would", "chunk", "content",
}


def normalize_space(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def stable_chunk_id(chunk: Dict[str, Any], fallback: int) -> str:
    file_name = normalize_space(chunk.get("file_name") or "chunk")
    chunk_id = normalize_space(chunk.get("global_chunk_id") or chunk.get("chunk_id") or fallback)
    return f"{file_name}:{chunk_id}"


def _tokenize(text: str) -> List[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.lower())
    return [word for word in words if word not in STOPWORDS]


def extract_keyphrases(text: str, max_phrases: int = 6) -> List[str]:
    """Extract compact lexical concepts without requiring an external model."""
    text = normalize_space(text)
    phrases: List[str] = []

    nounish = re.findall(
        r"\b(?:[A-Z][a-z0-9-]+|[a-z]+(?:-[a-z]+)?)"
        r"(?:\s+(?:[A-Z][a-z0-9-]+|[a-z]+(?:-[a-z]+)?)){1,4}\b",
        text,
    )
    for phrase in nounish:
        cleaned = normalize_space(phrase).strip(".,;:()[]")
        words = cleaned.lower().split()
        if (
            2 <= len(words) <= 5
            and not all(word in STOPWORDS for word in words)
            and len(cleaned) <= 70
        ):
            phrases.append(cleaned)

    counts = Counter(_tokenize(text))
    phrases.extend(word for word, _ in counts.most_common(max_phrases * 2))

    output: List[str] = []
    seen = set()
    for phrase in phrases:
        key = phrase.casefold()
        if key and key not in seen:
            seen.add(key)
            output.append(phrase)
        if len(output) >= max_phrases:
            break
    return output


def _chunk_index_from_label(label: Any) -> int | None:
    match = re.search(r"chunk\s*(\d+)", str(label or ""), re.IGNORECASE)
    return int(match.group(1)) if match else None


def _resolve_chunk_reference(reference: Any, chunks: List[Dict[str, Any]]) -> str | None:
    reference_text = normalize_space(reference)
    chunk_index = _chunk_index_from_label(reference_text)
    if chunk_index is not None and 1 <= chunk_index <= len(chunks):
        return stable_chunk_id(chunks[chunk_index - 1], chunk_index)
    reference_key = reference_text.casefold()
    for index, chunk in enumerate(chunks, 1):
        chunk_id = stable_chunk_id(chunk, index)
        if reference_key and reference_key == chunk_id.casefold():
            return chunk_id
    return None


def supporting_chunk_ids_from_record(
    qa_item: Dict[str, Any], chunks: List[Dict[str, Any]]
) -> List[str]:
    """Resolve only explicitly annotated supporting chunks.

    Deliberately returns an empty list when annotations are absent.  Treating
    every context chunk as supporting evidence creates false supervision.
    """
    ids: List[str] = []
    for fact in qa_item.get("supporting_facts", []) or []:
        if not isinstance(fact, dict):
            continue
        resolved = _resolve_chunk_reference(fact.get("chunk"), chunks)
        if resolved:
            ids.append(resolved)
    for span in qa_item.get("evidence_spans", []) or []:
        if not isinstance(span, dict):
            continue
        resolved = _resolve_chunk_reference(span.get("chunk"), chunks)
        if resolved:
            ids.append(resolved)
    return list(dict.fromkeys(ids))


def verified_supporting_chunk_ids(
    chunks: List[Dict[str, Any]],
    qa_item: Dict[str, Any],
    necessity_result: Dict[str, Any],
) -> tuple[List[str], str]:
    """Choose the strongest available evidence labels and record their source."""
    available = {
        stable_chunk_id(chunk, index)
        for index, chunk in enumerate(chunks or [], 1)
    }
    necessary = [
        str(chunk_id)
        for chunk_id in necessity_result.get("necessary_chunks", []) or []
        if str(chunk_id) in available
    ]
    if necessary:
        return list(dict.fromkeys(necessary)), "counterfactual_verifier"

    partial = [
        str(chunk_id)
        for chunk_id in necessity_result.get("supporting_chunks", []) or []
        if str(chunk_id) in available
    ]
    if partial:
        return list(dict.fromkeys(partial)), "single_chunk_verifier"

    explicit = supporting_chunk_ids_from_record(qa_item, chunks)
    if explicit:
        return explicit, "qa_evidence_annotations"
    return [], "unresolved"


def derive_hop_count(evidence_graph: Dict[str, Any]) -> int:
    """Return the canonical hop count: distinct required evidence chunks."""
    return len(list(dict.fromkeys(evidence_graph.get("supporting_chunk_ids", []) or [])))


def build_evidence_graph(
    chunks: List[Dict[str, Any]],
    qa_item: Dict[str, Any] | None = None,
    qa_metadata: Dict[str, Any] | None = None,
    necessity_result: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a compact evidence graph for a generated QA item.

    Nodes are source chunks and extracted concepts. Edges connect chunks to concepts,
    question/answer evidence, and adjacent supporting chunks to form an explicit
    multi-hop path.
    """
    qa_item = qa_item or {}
    qa_metadata = qa_metadata or {}
    necessity_result = necessity_result or {}
    necessary_ids = set(necessity_result.get("necessary_chunks", []) or [])
    redundant_ids = set(necessity_result.get("redundant_chunks", []) or [])
    supporting_ids, evidence_source = verified_supporting_chunk_ids(
        chunks or [], qa_item, necessity_result
    )
    supporting_id_set = set(supporting_ids)
    explicit_support_order = supporting_chunk_ids_from_record(qa_item, chunks or [])
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    chunk_ids: List[str] = []

    for idx, chunk in enumerate(chunks or [], 1):
        chunk_id = stable_chunk_id(chunk, idx)
        chunk_ids.append(chunk_id)
        content = normalize_space(chunk.get("content"))
        concepts = (
            qa_metadata.get("keywords_per_chunk", {}).get(f"chunk_{idx}")
            if isinstance(qa_metadata.get("keywords_per_chunk"), dict)
            else None
        )
        if not concepts:
            concepts = extract_keyphrases(content)

        if chunk_id in necessary_ids:
            necessity = "necessary"
        elif chunk_id in redundant_ids:
            necessity = "redundant"
        elif chunk_id in supporting_id_set:
            necessity = "supporting"
        else:
            necessity = "unverified"

        nodes.append({
            "id": chunk_id,
            "type": "chunk",
            "title": normalize_space(chunk.get("file_name") or f"Chunk {idx}"),
            "chunk_index": idx,
            "classification": chunk.get("classification", "seed" if idx == 1 else ""),
            "concepts": concepts,
            "necessity": necessity,
        })

        for concept in concepts[:6]:
            concept_id = f"concept::{normalize_space(concept).casefold()}"
            nodes.append({"id": concept_id, "type": "concept", "label": normalize_space(concept)})
            edges.append({
                "source": chunk_id,
                "target": concept_id,
                "type": "mentions",
                "weight": 1.0,
            })

    if len(explicit_support_order) >= 2:
        for left, right in zip(explicit_support_order, explicit_support_order[1:]):
            if left in supporting_ids and right in supporting_ids:
                edges.append({
                    "source": left,
                    "target": right,
                    "type": "multi_hop_bridge",
                    "weight": 1.0,
                    "basis": "declared_support_order",
                })

    for fact in qa_item.get("supporting_facts", []) or []:
        if not isinstance(fact, dict):
            continue
        chunk_index = _chunk_index_from_label(fact.get("chunk"))
        if chunk_index is None or chunk_index < 1 or chunk_index > len(chunk_ids):
            continue
        fact_id = f"fact::{len(nodes)}"
        nodes.append({"id": fact_id, "type": "supporting_fact", "text": normalize_space(fact.get("fact"))})
        edges.append({"source": chunk_ids[chunk_index - 1], "target": fact_id, "type": "supports"})

    for span in qa_item.get("evidence_spans", []) or []:
        if not isinstance(span, dict):
            continue
        chunk_index = _chunk_index_from_label(span.get("chunk"))
        if chunk_index is None or chunk_index < 1 or chunk_index > len(chunk_ids):
            continue
        span_id = f"span::{len(nodes)}"
        nodes.append({"id": span_id, "type": "evidence_span", "text": normalize_space(span.get("span"))})
        edges.append({"source": chunk_ids[chunk_index - 1], "target": span_id, "type": "grounds"})

    deduped_nodes = []
    seen_nodes = set()
    for node in nodes:
        node_id = node["id"]
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            deduped_nodes.append(node)

    return {
        "nodes": deduped_nodes,
        "edges": edges,
        "supporting_chunk_ids": supporting_ids,
        "hop_count": len(supporting_ids),
        "path_length": max(0, len(explicit_support_order) - 1),
        "evidence_source": evidence_source,
        "evidence_resolved": len(supporting_ids) >= 2,
        "necessary_chunk_ids": list(necessary_ids),
        "redundant_chunk_ids": list(redundant_ids),
        "construction": (
            "counterfactual_minimal_evidence_graph"
            if evidence_source == "counterfactual_verifier"
            else "verified_partial_evidence_graph"
            if evidence_source == "single_chunk_verifier"
            else "annotated_evidence_graph"
            if evidence_source == "qa_evidence_annotations"
            else "unresolved_evidence_graph"
        ),
    }


def build_search_trajectory(context_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten context-completion logs into Search-R1-style search supervision."""
    trajectory: List[Dict[str, Any]] = []
    for iter_log in context_result.get("iteration_logs", []) or []:
        depth = iter_log.get("depth")
        model_route = iter_log.get("model_route", {})
        by_query: Dict[str, Dict[str, Any]] = {}
        for query in iter_log.get("search_strings") or []:
            by_query[query] = {
                "depth": depth,
                "query": query,
                "model_route": model_route,
                "retrieved": [],
                "selected": [],
            }
        for item in iter_log.get("retrieved_chunks", []) or []:
            query = item.get("search_query") or ""
            step = by_query.setdefault(
                query,
                {
                    "depth": depth,
                    "query": query,
                    "model_route": model_route,
                    "retrieved": [],
                    "selected": [],
                },
            )
            chunk_ref = {
                "chunk_id": item.get("chunk_id"),
                "file_name": item.get("file_name"),
                "score": item.get("score"),
                "rank": item.get("rank"),
                "verdict": item.get("verdict"),
                "reason": item.get("reason"),
                "action": (
                    "select"
                    if item.get("verdict") in {"EXPLANATORY", "RELATED"}
                    else "reject"
                ),
            }
            step["retrieved"].append(chunk_ref)
            if item.get("verdict") in {"EXPLANATORY", "RELATED"}:
                step["selected"].append(chunk_ref)
        trajectory.extend(by_query.values())
    if trajectory:
        trajectory[-1]["termination"] = {
            "status": context_result.get("status"),
            "reason": context_result.get("termination_reason"),
        }
    return trajectory


def ensure_short_answers(qa_item: Dict[str, Any], max_words: int = 8) -> List[str]:
    """Return one canonical EM answer without inventing aliases or rewrites."""
    existing = qa_item.get("short_answers") or qa_item.get("answer_aliases") or qa_item.get("aliases")
    if isinstance(existing, str):
        existing = [existing]
    if isinstance(existing, list) and any(str(item).strip() for item in existing):
        return _unique_answers([str(item) for item in existing])

    answer = normalize_space(qa_item.get("answer"))
    return _unique_answers([answer]) if answer else []


def _unique_answers(items: List[str]) -> List[str]:
    output: List[str] = []
    seen = set()
    for item in items:
        cleaned = normalize_space(item).strip(" .;,")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output
