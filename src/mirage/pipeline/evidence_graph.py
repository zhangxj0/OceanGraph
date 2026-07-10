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


def _supporting_chunk_ids(qa_item: Dict[str, Any], chunks: List[Dict[str, Any]]) -> List[str]:
    ids: List[str] = []
    for fact in qa_item.get("supporting_facts", []) or []:
        if not isinstance(fact, dict):
            continue
        chunk_index = _chunk_index_from_label(fact.get("chunk"))
        if chunk_index is not None and 1 <= chunk_index <= len(chunks):
            ids.append(stable_chunk_id(chunks[chunk_index - 1], chunk_index))
    for span in qa_item.get("evidence_spans", []) or []:
        if not isinstance(span, dict):
            continue
        chunk_index = _chunk_index_from_label(span.get("chunk"))
        if chunk_index is not None and 1 <= chunk_index <= len(chunks):
            ids.append(stable_chunk_id(chunks[chunk_index - 1], chunk_index))
    if not ids:
        ids = [stable_chunk_id(chunk, idx) for idx, chunk in enumerate(chunks, 1)]
    return list(dict.fromkeys(ids))


def build_evidence_graph(
    chunks: List[Dict[str, Any]],
    qa_item: Dict[str, Any] | None = None,
    qa_metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a compact evidence graph for a generated QA item.

    Nodes are source chunks and extracted concepts. Edges connect chunks to concepts,
    question/answer evidence, and adjacent supporting chunks to form an explicit
    multi-hop path.
    """
    qa_item = qa_item or {}
    qa_metadata = qa_metadata or {}
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

        nodes.append({
            "id": chunk_id,
            "type": "chunk",
            "title": normalize_space(chunk.get("file_name") or f"Chunk {idx}"),
            "chunk_index": idx,
            "classification": chunk.get("classification", "seed" if idx == 1 else ""),
            "concepts": concepts,
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

    supporting_ids = _supporting_chunk_ids(qa_item, chunks or [])
    for left, right in zip(supporting_ids, supporting_ids[1:]):
        edges.append({"source": left, "target": right, "type": "multi_hop_bridge", "weight": 1.0})

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
        "path_length": max(0, len(supporting_ids) - 1),
        "construction": "lexical_concepts_with_supporting_fact_edges",
    }


def build_search_trajectory(context_result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten context-completion logs into Search-R1-style search supervision."""
    trajectory: List[Dict[str, Any]] = []
    for iter_log in context_result.get("iteration_logs", []) or []:
        depth = iter_log.get("depth")
        by_query: Dict[str, Dict[str, Any]] = {}
        for query in iter_log.get("search_strings") or []:
            by_query[query] = {"depth": depth, "query": query, "retrieved": [], "selected": []}
        for item in iter_log.get("retrieved_chunks", []) or []:
            query = item.get("search_query") or ""
            step = by_query.setdefault(
                query, {"depth": depth, "query": query, "retrieved": [], "selected": []}
            )
            chunk_ref = {
                "chunk_id": item.get("chunk_id"),
                "file_name": item.get("file_name"),
                "score": item.get("score"),
                "verdict": item.get("verdict"),
            }
            step["retrieved"].append(chunk_ref)
            if item.get("verdict") in {"EXPLANATORY", "RELATED"}:
                step["selected"].append(chunk_ref)
        trajectory.extend(by_query.values())
    return trajectory


def ensure_short_answers(qa_item: Dict[str, Any], max_words: int = 12) -> List[str]:
    """Create minimal answer aliases when the generator did not emit short_answers."""
    existing = qa_item.get("short_answers") or qa_item.get("answer_aliases") or qa_item.get("aliases")
    if isinstance(existing, str):
        existing = [existing]
    if isinstance(existing, list) and any(str(item).strip() for item in existing):
        return _unique_answers([str(item) for item in existing])

    answer = normalize_space(qa_item.get("answer"))
    answer_type = normalize_space(qa_item.get("answer_type")).lower()
    candidates: List[str] = []

    if answer_type in {"yes_no", "boolean"}:
        if answer.lower().startswith("yes"):
            candidates.append("yes")
        elif answer.lower().startswith("no"):
            candidates.append("no")

    if answer_type == "numeric":
        match = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?(?:\s*%|\s*[A-Za-z/]+)?", answer)
        if match:
            candidates.append(match.group(0))

    first = re.split(r"(?<=[.!?])\s+", answer, maxsplit=1)[0]
    first = re.sub(r"^the\s+(?:two|three|four|five)\s+[^.]{0,80}?\s+are\s+", "", first, flags=re.I)
    first = re.sub(r"^the\s+[^.]{0,80}?\s+(?:is|are)\s+", "", first, flags=re.I)
    if len(first.split()) > max_words:
        first = re.split(
            r"\s+(?:because|by|through|when|while|which|that|, reducing|, isolating)\s+",
            first,
            maxsplit=1,
            flags=re.I,
        )[0]
    candidates.append(first)

    cleaned = _unique_answers(candidates)
    if cleaned and " and " in cleaned[0].lower() and "," not in cleaned[0]:
        parts = re.split(r"\s+and\s+", cleaned[0], maxsplit=1, flags=re.I)
        if len(parts) == 2:
            cleaned.append(f"{parts[1].strip(' .;,')} and {parts[0].strip(' .;,')}")
    return _unique_answers(cleaned)


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
