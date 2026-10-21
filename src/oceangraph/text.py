"""Text-only normalization helpers for OceanGraph dataset records."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List
import re


def is_metadata_only_chunk(text: str) -> bool:
    """Recognize a complete bibliographic YAML block without any science body."""
    match = re.fullmatch(r"---[ \t]*\r?\n(.*?)\r?\n---[ \t]*", str(text).strip(), re.DOTALL)
    if not match:
        return False
    keys = set(re.findall(r"(?m)^([a-z_]+)\s*:", match.group(1)))
    return bool(
        keys & {"document_id", "source", "doi", "url"}
        and len(keys & {"document_id", "title", "authors", "publication_year",
                        "source", "doi", "url", "license", "domain", "subdomain"}) >= 2
    )


def sanitize_text_chunks(chunks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Copy chunks while removing visual inputs and image-only metadata."""
    sanitized: List[Dict[str, Any]] = []
    for chunk in chunks:
        normalized = dict(chunk)
        content = str(normalized.get("content") or normalized.get("text") or "").strip()
        if not content:
            continue
        normalized["artifact"] = []
        normalized["image_path"] = None
        if str(normalized.get("chunk_type", "")).lower() in {"image", "standalone image"}:
            normalized["chunk_type"] = "text"
        sanitized.append(normalized)
    return sanitized
