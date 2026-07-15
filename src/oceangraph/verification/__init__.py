"""Deterministic verification gates for OceanGraph datasets."""

from oceangraph.verification.necessity import evaluate_multihop_gate
from oceangraph.verification.quality import has_visible_self_correction

__all__ = ["evaluate_multihop_gate", "has_visible_self_correction"]
