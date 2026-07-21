"""Canonical five-domain ocean taxonomy used by generated dataset labels."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Mapping

import yaml


TAXONOMY_PATH = Path(__file__).resolve().parents[1] / "ocean_taxonomy.yaml"

_ANSWER_TYPE_ALIASES = {
    "entity": "entity",
    "name": "entity",
    "numeric": "numeric",
    "number": "numeric",
    "numerical": "numeric",
    "date": "date",
    "year": "date",
    "yes_no": "yes_no",
    "yes/no": "yes_no",
    "boolean": "yes_no",
    "short_text": "short_text",
    "short text": "short_text",
    "text": "short_text",
    "description": "short_text",
}


@lru_cache(maxsize=1)
def load_ocean_taxonomy() -> Dict[str, Any]:
    with TAXONOMY_PATH.open("r", encoding="utf-8") as handle:
        taxonomy = yaml.safe_load(handle) or {}
    domains = taxonomy.get("domains") or []
    if len(domains) != 5:
        raise ValueError("OceanGraph taxonomy must define exactly five primary domains")
    return taxonomy


def taxonomy_domain_ids() -> List[str]:
    return [str(item["id"]) for item in load_ocean_taxonomy()["domains"]]


def taxonomy_answer_types() -> List[str]:
    """Return the canonical answer labels allowed by the dataset contract."""
    return [str(item) for item in load_ocean_taxonomy().get("answer_types") or []]


def normalize_answer_type(value: str | None) -> str:
    """Normalize harmless legacy labels without accepting open-ended lists."""
    normalized = str(value or "").strip().casefold().replace("-", "_")
    canonical = _ANSWER_TYPE_ALIASES.get(normalized, normalized)
    return canonical if canonical in set(taxonomy_answer_types()) else ""


def _match_alias(value: str, domain: Mapping[str, Any]) -> bool:
    normalized = value.strip().casefold().replace("-", "_").replace(" ", "_")
    candidates = [domain.get("id", ""), domain.get("title", ""), *(domain.get("aliases") or [])]
    for candidate in candidates:
        candidate_key = str(candidate).strip().casefold().replace("-", "_").replace(" ", "_")
        if normalized and candidate_key and (
            normalized == candidate_key
            or candidate_key in normalized
            or normalized in candidate_key
        ):
            return True
    return False


def normalize_ocean_subdomain(
    value: str | None,
    *,
    text: str = "",
    domain_hint: str = "",
) -> str:
    """Map free-form generator output to one stable five-domain identifier."""
    taxonomy = load_ocean_taxonomy()
    domains = taxonomy["domains"]
    for candidate in (value or "", domain_hint or ""):
        for domain in domains:
            if _match_alias(candidate, domain):
                return str(domain["id"])

    haystack = " ".join((value or "", domain_hint or "", text or "")).casefold()
    scored = []
    for index, domain in enumerate(domains):
        score = sum(
            1
            for keyword in domain.get("keywords") or []
            if str(keyword).casefold() in haystack
        )
        scored.append((score, -index, str(domain["id"])))
    best_score, _, best_id = max(scored)
    return best_id if best_score > 0 else ""


def taxonomy_metadata() -> Dict[str, Any]:
    taxonomy = load_ocean_taxonomy()
    return {
        "schema_version": str(taxonomy.get("schema_version", "")),
        "domain_ids": taxonomy_domain_ids(),
        "answer_types": taxonomy_answer_types(),
    }


__all__ = [
    "load_ocean_taxonomy",
    "normalize_answer_type",
    "normalize_ocean_subdomain",
    "taxonomy_answer_types",
    "taxonomy_domain_ids",
    "taxonomy_metadata",
]
