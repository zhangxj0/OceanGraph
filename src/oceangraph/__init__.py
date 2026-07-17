"""Public API for the OceanGraph dataset generation framework."""

from .api import OceanGraph, OceanGraphConfig, OceanGraphResults
from .agents import (
    AGENT_ARCHITECTURE_VERSION,
    AGENT_SPECS,
    AgentSpec,
    CorpusAgent,
    EvidenceAgent,
    QAAgent,
    VerifierAgent,
    get_agent_manifest,
)

FRAMEWORK_NAME = "OceanGraph-R1"
FRAMEWORK_VERSION = "2.2.0"

__all__ = [
    "AGENT_ARCHITECTURE_VERSION",
    "AGENT_SPECS",
    "AgentSpec",
    "CorpusAgent",
    "EvidenceAgent",
    "FRAMEWORK_NAME",
    "FRAMEWORK_VERSION",
    "OceanGraph",
    "OceanGraphConfig",
    "OceanGraphResults",
    "QAAgent",
    "VerifierAgent",
    "get_agent_manifest",
]
