"""Public API for the OceanGraph dataset generation framework."""

from .api import OceanGraph, OceanGraphConfig, OceanGraphResults
from .agents import (
    AGENT_ARCHITECTURE_VERSION,
    AGENT_SPECS,
    AgentCoordinator,
    AgentSpec,
    AgentState,
    CorpusAgent,
    EvidenceAgent,
    FeedbackRoute,
    QAAgent,
    VerifierAgent,
    get_agent_manifest,
)

FRAMEWORK_NAME = "OceanGraph-R1"
FRAMEWORK_VERSION = "3.0.0"
__version__ = FRAMEWORK_VERSION

__all__ = [
    "AGENT_ARCHITECTURE_VERSION",
    "AGENT_SPECS",
    "AgentCoordinator",
    "AgentSpec",
    "AgentState",
    "CorpusAgent",
    "EvidenceAgent",
    "FeedbackRoute",
    "FRAMEWORK_NAME",
    "FRAMEWORK_VERSION",
    "OceanGraph",
    "OceanGraphConfig",
    "OceanGraphResults",
    "QAAgent",
    "VerifierAgent",
    "get_agent_manifest",
    "__version__",
]
