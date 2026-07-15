"""Deterministic QA quality gates that do not require model calls."""

import re


def has_visible_self_correction(answer: str) -> bool:
    """Detect drafting or self-correction language that invalidates a final answer."""
    if not answer:
        return False
    patterns = [
        r"\bwait\s*[,.:;!?]",
        r"\blet me (?:re-?read|recalculate|re-evaluate|check|correct)\b",
        r"\b(?:recalculation|self-correction|correction)\s*:",
        r"\bi (?:need to|must|should) (?:correct|revise|reconsider)\b",
    ]
    return any(re.search(pattern, answer, re.IGNORECASE) for pattern in patterns)
