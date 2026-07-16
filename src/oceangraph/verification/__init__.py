"""Deterministic verification gates for OceanGraph datasets."""

from oceangraph.verification.necessity import evaluate_multihop_gate
from oceangraph.verification.quality import (
    atomic_qa_violations,
    has_visible_self_correction,
    is_atomic_short_answer_qa,
)

__all__ = [
    "atomic_qa_violations",
    "evaluate_multihop_gate",
    "has_visible_self_correction",
    "is_atomic_short_answer_qa",
]
