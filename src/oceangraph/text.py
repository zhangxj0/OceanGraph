"""Text-only normalization helpers for OceanGraph dataset records."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


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
