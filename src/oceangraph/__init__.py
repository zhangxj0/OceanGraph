"""Public API for the OceanGraph dataset generation framework."""

from .api import OceanGraph, OceanGraphConfig, OceanGraphResults

FRAMEWORK_NAME = "OceanGraph-R1"
FRAMEWORK_VERSION = "2.1.0"

__all__ = [
    "FRAMEWORK_NAME",
    "FRAMEWORK_VERSION",
    "OceanGraph",
    "OceanGraphConfig",
    "OceanGraphResults",
]
