"""Runtime roles for the four-agent OceanGraph v2.2 architecture.

The agents in this module are deliberately thin orchestration boundaries.  They
reuse the validated v2.1 implementation while making ownership explicit:

``Corpus -> Evidence -> QA -> Verifier``.

Keeping the wrappers small avoids changing retrieval or acceptance semantics,
while the emitted trace makes the paper-facing architecture auditable in every
dataset record.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Tuple


AGENT_ARCHITECTURE_VERSION = "2.2.1"


@dataclass(frozen=True)
class AgentSpec:
    """Stable description of one runtime role."""

    agent_id: str
    name: str
    model_stages: Tuple[str, ...]
    responsibilities: Tuple[str, ...]
    input_artifacts: Tuple[str, ...]
    output_artifacts: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "model_stages": list(self.model_stages),
            "responsibilities": list(self.responsibilities),
            "input_artifacts": list(self.input_artifacts),
            "output_artifacts": list(self.output_artifacts),
        }


AGENT_SPECS: Tuple[AgentSpec, ...] = (
    AgentSpec(
        agent_id="corpus",
        name="Corpus Agent",
        model_stages=("corpus",),
        responsibilities=(
            "domain_recognition",
            "chunking_and_parsing",
            "taxonomy_and_indexing",
        ),
        input_artifacts=("source_documents",),
        output_artifacts=("chunks", "domain_taxonomy", "vector_index"),
    ),
    AgentSpec(
        agent_id="evidence",
        name="Evidence Agent",
        model_stages=("retrieval",),
        responsibilities=(
            "gap_detection",
            "evidence_retrieval",
            "context_completion",
        ),
        input_artifacts=("seed_chunk", "vector_index"),
        output_artifacts=("completed_context", "search_history"),
    ),
    AgentSpec(
        agent_id="qa",
        name="QA Agent",
        model_stages=("generation", "selection", "correction"),
        responsibilities=(
            "qa_synthesis",
            "subquestion_chaining",
            "reasoning_path_assembly",
        ),
        input_artifacts=("completed_context",),
        output_artifacts=("qa_candidates", "reasoning_annotations"),
    ),
    AgentSpec(
        agent_id="verifier",
        name="Verifier Agent",
        model_stages=("verification",),
        responsibilities=(
            "atomicity_check",
            "evidence_grounding",
            "multihop_necessity",
        ),
        input_artifacts=("qa_candidate", "completed_context"),
        output_artifacts=("verification_decision", "evidence_graph"),
    ),
)

_AGENT_BY_ID = {spec.agent_id: spec for spec in AGENT_SPECS}


def get_agent_manifest() -> List[Dict[str, Any]]:
    """Return the ordered, JSON-serializable four-agent manifest."""

    return [spec.to_dict() for spec in AGENT_SPECS]


def make_agent_event(
    agent_id: str,
    *,
    status: str,
    outputs: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build one stable provenance event for a dataset record."""

    spec = _AGENT_BY_ID[agent_id]
    event: Dict[str, Any] = {
        "agent_id": spec.agent_id,
        "agent_name": spec.name,
        "status": status,
        "actions": list(spec.responsibilities),
    }
    if outputs:
        event["outputs"] = dict(outputs)
    return event


class CorpusAgent:
    """Own corpus loading, parsing, indexing, and domain recognition calls."""

    spec = _AGENT_BY_ID["corpus"]

    def load_chunks(self, path: str, loader: Callable[[str], list]) -> list:
        return loader(path)

    def build_chunks(
        self,
        input_dir: str,
        output_file: str,
        converter: Callable[..., list],
        checkpoint_manager: Any,
    ) -> list:
        return converter(input_dir, output_file, checkpoint_manager)

    def build_index(
        self,
        chunks: list,
        chunks_file: str,
        embeddings_dir: str,
        indexer: Callable[..., tuple],
    ) -> tuple:
        return indexer(chunks, chunks_file, embeddings_dir)

    def recognize_domain(
        self,
        chunks_file: str,
        embeddings: Any,
        chunk_ids: list,
        recognizer: Callable[..., tuple],
    ) -> tuple:
        return recognizer(chunks_file, embeddings=embeddings, chunk_ids=chunk_ids)

    def trace_source(
        self,
        *,
        chunk_id: str,
        file_name: str,
        domain: str,
    ) -> Dict[str, Any]:
        return make_agent_event(
            self.spec.agent_id,
            status="completed",
            outputs={
                "chunk_id": chunk_id,
                "file_name": file_name,
                "domain": domain,
            },
        )


class EvidenceAgent:
    """Own multi-hop evidence retrieval and context completion."""

    spec = _AGENT_BY_ID["evidence"]

    def complete_context(self, **kwargs: Any) -> Dict[str, Any]:
        from oceangraph.pipeline.context import build_complete_context

        return build_complete_context(**kwargs)

    def expand_context_from_feedback(
        self,
        result: Mapping[str, Any],
        *,
        query: str,
        top_k: int = 2,
    ) -> Dict[str, Any]:
        """Retrieve additional evidence after a verifier requests expansion.

        This bounded operation preserves the existing context and appends only
        distinct chunks.  It gives the coordinator a real Verifier -> Evidence
        transition instead of treating every failure as a QA-rewrite problem.
        """
        from oceangraph.pipeline.context import retrieve_chunks_for_query

        expanded = dict(result)
        current_chunks = [dict(chunk) for chunk in result.get("chunks", []) or []]
        existing_ids = {
            (str(chunk.get("file_name", "")), str(chunk.get("chunk_id", "")))
            for chunk in current_chunks
        }
        retrieved = retrieve_chunks_for_query(query, top_k=max(1, int(top_k)))
        added: List[Dict[str, Any]] = []
        for chunk in retrieved:
            identity = (
                str(chunk.get("file_name", "")),
                str(chunk.get("chunk_id", "")),
            )
            if identity in existing_ids:
                continue
            existing_ids.add(identity)
            copied = dict(chunk)
            current_chunks.append(copied)
            added.append(copied)

        prior_added = list(result.get("chunks_added", []) or [])
        prior_added.extend(
            {
                "file_name": chunk.get("file_name", "unknown"),
                "chunk_id": chunk.get("chunk_id", ""),
            }
            for chunk in added
        )
        search_history = list(result.get("search_history", []) or [])
        search_history.append(query)
        iteration_logs = list(result.get("iteration_logs", []) or [])
        iteration_logs.append(
            {
                "depth": int(result.get("depth", 0) or 0) + 1,
                "source": "verifier_feedback",
                "search_strings": [query],
                "retrieved_chunks": [
                    {
                        "search_query": query,
                        "chunk_id": chunk.get("chunk_id"),
                        "file_name": chunk.get("file_name"),
                        "score": chunk.get("score"),
                        "verdict": "RELATED",
                        "reason": "Retrieved from verifier feedback",
                    }
                    for chunk in added
                ],
            }
        )
        expanded.update(
            {
                "chunks": current_chunks,
                "context": "\n\n".join(
                    str(chunk.get("content", "")) for chunk in current_chunks
                ),
                "status": "EXPANDED_FROM_VERIFIER" if added else result.get("status"),
                "depth": int(result.get("depth", 0) or 0) + (1 if added else 0),
                "hop_count": len(current_chunks),
                "retrieval_hop_count": max(0, len(current_chunks) - 1),
                "context_chunk_count": len(current_chunks),
                "chunks_added": prior_added,
                "search_history": search_history,
                "iteration_logs": iteration_logs,
                "feedback_chunks_added": len(added),
            }
        )
        return expanded

    def trace_context(self, result: Mapping[str, Any]) -> Dict[str, Any]:
        return make_agent_event(
            self.spec.agent_id,
            status="completed",
            outputs={
                "context_status": result.get("status", ""),
                "depth_reached": result.get("depth", 0),
                "context_chunk_count": result.get(
                    "context_chunk_count", len(result.get("chunks", []) or [])
                ),
                "retrieval_hop_count": result.get("retrieval_hop_count", 0),
                "chunks_added": len(result.get("chunks_added", []) or []),
            },
        )


class QAAgent:
    """Own candidate synthesis, selection, and verifier-guided correction."""

    spec = _AGENT_BY_ID["qa"]

    def generate(
        self,
        chunks: List[Dict[str, Any]],
        expert_persona: str,
        domain: str,
    ) -> tuple:
        from oceangraph.pipeline.qa_generator import generate_qa

        return generate_qa(chunks, expert_persona, domain)

    def select(
        self,
        qa_pairs: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
        expert_persona: str,
        domain: str,
        *,
        use_model_review: bool,
        max_answer_words: int = 12,
        max_answer_cjk_chars: int = 16,
    ) -> tuple:
        from oceangraph.pipeline.qa_generator import select_qa_pairs

        return select_qa_pairs(
            qa_pairs,
            chunks,
            expert_persona,
            domain,
            use_model_review=use_model_review,
            max_answer_words=max_answer_words,
            max_answer_cjk_chars=max_answer_cjk_chars,
        )

    def correct(
        self,
        chunks: List[Dict[str, Any]],
        failed_qa_pairs: List[Dict[str, Any]],
        expert_persona: str,
        domain: str,
    ) -> List[Dict[str, Any]]:
        from oceangraph.pipeline.qa_generator import correct_failed_qa

        return correct_failed_qa(chunks, failed_qa_pairs, expert_persona, domain)

    def prepare_candidate(self, qa_pair: Dict[str, Any]) -> Dict[str, Any]:
        from oceangraph.pipeline.evidence_graph import ensure_short_answers

        qa_pair["short_answers"] = ensure_short_answers(qa_pair)
        return qa_pair

    def trace_candidate(
        self,
        qa_pair: Mapping[str, Any],
        *,
        status: str,
    ) -> Dict[str, Any]:
        return make_agent_event(
            self.spec.agent_id,
            status=status,
            outputs={
                "selection_status": qa_pair.get("selection_status", status.upper()),
                "declared_hop_count": qa_pair.get("declared_hop_count", 0),
                "subquestion_count": len(qa_pair.get("sub_questions", []) or []),
            },
        )


@dataclass
class VerificationDecision:
    """All verifier outputs required by the engine and exported provenance."""

    verification_result: str
    multihop_necessity_result: Dict[str, Any]
    evidence_graph: Dict[str, Any]
    quality_violations: List[str]
    verification_passed: bool
    multihop_passed: bool
    verifier_uncertain: bool

    @property
    def accepted(self) -> bool:
        return self.verification_passed and self.multihop_passed

    def trace_event(self) -> Dict[str, Any]:
        return make_agent_event(
            "verifier",
            status="accepted" if self.accepted else "rejected",
            outputs={
                "atomic": not self.quality_violations,
                "grounded": self.verification_passed,
                "necessary": self.multihop_passed,
                "auditable": bool(self.evidence_graph.get("nodes")),
                "quality_violations": list(self.quality_violations),
                "multihop_status": self.multihop_necessity_result.get(
                    "status", "not_checked"
                ),
            },
        )


@dataclass(frozen=True)
class FeedbackRoute:
    """Coordinator decision following one verifier result."""

    target: str
    action: str
    reason: str


@dataclass
class AgentState:
    """Per-candidate shared state for auditable multi-agent coordination."""

    seed_chunk_id: str
    candidate_id: str
    status: str = "running"
    agent_trace: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    qa_revision_count: int = 0
    evidence_retry_count: int = 0

    def record_event(self, event: Mapping[str, Any]) -> Dict[str, Any]:
        recorded = dict(event)
        recorded["sequence"] = len(self.agent_trace) + 1
        self.agent_trace.append(recorded)
        return recorded

    def record_message(
        self,
        *,
        source: str,
        target: str,
        message_type: str,
        reason: str,
        payload: Mapping[str, Any] | None = None,
    ) -> Dict[str, Any]:
        message = {
            "sequence": len(self.messages) + 1,
            "source": source,
            "target": target,
            "type": message_type,
            "reason": reason,
            "payload": dict(payload or {}),
        }
        self.messages.append(message)
        return message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed_chunk_id": self.seed_chunk_id,
            "candidate_id": self.candidate_id,
            "status": self.status,
            "qa_revision_count": self.qa_revision_count,
            "evidence_retry_count": self.evidence_retry_count,
            "messages": [dict(message) for message in self.messages],
        }


class AgentCoordinator:
    """Stateful controller for four-agent execution and verifier feedback."""

    def __init__(self, *, max_qa_revisions: int = 1, max_evidence_retries: int = 1):
        self.max_qa_revisions = max(0, int(max_qa_revisions))
        self.max_evidence_retries = max(0, int(max_evidence_retries))

    def start_candidate(
        self,
        *,
        seed_chunk_id: str,
        candidate_id: str,
        base_events: List[Mapping[str, Any]] | None = None,
    ) -> AgentState:
        state = AgentState(
            seed_chunk_id=str(seed_chunk_id),
            candidate_id=str(candidate_id),
        )
        for event in base_events or []:
            state.record_event(event)
        return state

    def record_qa(
        self,
        state: AgentState,
        event: Mapping[str, Any],
    ) -> None:
        state.record_event(event)

    def review(
        self,
        state: AgentState,
        decision: VerificationDecision,
    ) -> FeedbackRoute:
        """Record a verifier decision and choose the next responsible agent."""
        multihop_status = str(
            decision.multihop_necessity_result.get("status", "NOT_CHECKED")
        )
        if decision.accepted:
            route = FeedbackRoute("final", "accept", "verification_passed")
            state.status = "accepted"
        elif decision.verifier_uncertain:
            route = FeedbackRoute("final", "reject", multihop_status)
            state.status = "rejected_uncertain"
        elif (
            multihop_status == "INSUFFICIENT_CHUNKS"
            and state.evidence_retry_count < self.max_evidence_retries
        ):
            state.evidence_retry_count += 1
            route = FeedbackRoute(
                "evidence",
                "expand_evidence",
                "verifier_found_insufficient_chunks",
            )
            state.status = "awaiting_evidence"
        elif state.qa_revision_count < self.max_qa_revisions:
            state.qa_revision_count += 1
            route = FeedbackRoute("qa", "revise_candidate", multihop_status)
            state.status = "awaiting_qa_revision"
        else:
            route = FeedbackRoute("final", "reject", "revision_budget_exhausted")
            state.status = "rejected"

        verifier_event = decision.trace_event()
        verifier_outputs = dict(verifier_event.get("outputs", {}))
        verifier_outputs["feedback_target"] = route.target
        verifier_outputs["feedback_action"] = route.action
        verifier_event["outputs"] = verifier_outputs
        state.record_event(verifier_event)
        if route.target != "final":
            state.record_message(
                source="verifier",
                target=route.target,
                message_type="verification_feedback",
                reason=route.reason,
                payload={
                    "multihop_status": multihop_status,
                    "quality_violations": list(decision.quality_violations),
                },
            )
        return route


class VerifierAgent:
    """Own atomicity, grounding, and multi-hop necessity decisions."""

    spec = _AGENT_BY_ID["verifier"]

    def __init__(
        self,
        *,
        strict_multihop: bool,
        min_supporting_chunks: int,
        counterfactual_verification: bool,
        verification_mode: str,
        max_verification_chunks: int,
        max_unknown_chunks: int,
        verification_profile: str = "legacy",
        max_answer_words: int = 12,
        max_answer_cjk_chars: int = 16,
    ) -> None:
        self.strict_multihop = strict_multihop
        self.min_supporting_chunks = min_supporting_chunks
        self.counterfactual_verification = counterfactual_verification
        self.verification_mode = verification_mode
        self.max_verification_chunks = max_verification_chunks
        self.max_unknown_chunks = max_unknown_chunks
        self.verification_profile = str(verification_profile or "legacy").lower()
        self.max_answer_words = max(1, int(max_answer_words))
        self.max_answer_cjk_chars = max(1, int(max_answer_cjk_chars))

    def verify(
        self,
        chunks: List[Dict[str, Any]],
        qa_pair: Dict[str, Any],
        qa_metadata: Dict[str, Any],
        expert_persona: str,
        domain: str,
    ) -> VerificationDecision:
        from oceangraph.pipeline.evidence_graph import build_evidence_graph
        from oceangraph.pipeline.qa_generator import (
            is_multihop_necessity_successful,
            is_verification_successful,
            verify_qa_cost_efficient,
            verify_multihop_necessity,
            verify_qa,
        )
        from oceangraph.verification.quality import atomic_qa_violations

        quality_violations = atomic_qa_violations(
            qa_pair["question"],
            qa_pair["answer"],
            qa_pair.get("short_answers"),
            max_answer_words=self.max_answer_words,
            max_answer_cjk_chars=self.max_answer_cjk_chars,
        )
        if quality_violations:
            multihop_necessity = {
                "status": "LOCAL_QUALITY_GATE_FAILED",
                "passes": False,
                "supporting_chunks": [],
                "verification_profile": self.verification_profile,
                "verification_api_calls": 0,
            }
            evidence_graph = build_evidence_graph(
                chunks,
                qa_item=qa_pair,
                qa_metadata=qa_metadata,
                necessity_result=multihop_necessity,
            )
            return VerificationDecision(
                verification_result=(
                    "LOCAL_REJECTED: " + ", ".join(quality_violations)
                ),
                multihop_necessity_result=multihop_necessity,
                evidence_graph=evidence_graph,
                quality_violations=quality_violations,
                verification_passed=False,
                multihop_passed=False,
                verifier_uncertain=False,
            )

        if self.verification_profile == "cost_efficient":
            multihop_necessity = verify_qa_cost_efficient(
                chunks,
                qa_pair,
                expert_persona,
                domain,
                min_supporting_chunks=self.min_supporting_chunks,
                max_verification_chunks=self.max_verification_chunks,
            )
            verification = str(
                multihop_necessity.get("raw_response")
                or multihop_necessity.get("reason")
                or multihop_necessity.get("status", "")
            )
            verification_passed = bool(
                multihop_necessity.get("basic_checks_passed")
            )
            multihop_passed = (
                bool(multihop_necessity.get("passes"))
                if self.strict_multihop
                else verification_passed
            )
        else:
            verification = verify_qa(
                chunks,
                qa_pair["question"],
                qa_pair["answer"],
                expert_persona,
                domain,
            )
            multihop_necessity = {}
            if self.strict_multihop:
                multihop_necessity = verify_multihop_necessity(
                    chunks,
                    qa_pair["question"],
                    qa_pair["answer"],
                    expert_persona,
                    domain,
                    min_supporting_chunks=self.min_supporting_chunks,
                    counterfactual_verification=self.counterfactual_verification,
                    qa_pair=qa_pair,
                    verification_mode=self.verification_mode,
                    max_verification_chunks=self.max_verification_chunks,
                    max_unknown_chunks=self.max_unknown_chunks,
                )
            verification_passed = is_verification_successful(
                verification,
                question=qa_pair["question"],
                answer=qa_pair["answer"],
                short_answers=qa_pair.get("short_answers"),
                chunks=chunks,
            )
            multihop_passed = (
                not self.strict_multihop
                or is_multihop_necessity_successful(multihop_necessity)
            )

        evidence_graph = build_evidence_graph(
            chunks,
            qa_pair,
            qa_metadata,
            necessity_result=multihop_necessity,
        )
        verifier_uncertain = str(multihop_necessity.get("status", "")).startswith(
            "UNKNOWN_"
        )
        return VerificationDecision(
            verification_result=verification,
            multihop_necessity_result=multihop_necessity,
            evidence_graph=evidence_graph,
            quality_violations=quality_violations,
            verification_passed=verification_passed,
            multihop_passed=multihop_passed,
            verifier_uncertain=verifier_uncertain,
        )


__all__ = [
    "AGENT_ARCHITECTURE_VERSION",
    "AGENT_SPECS",
    "AgentSpec",
    "AgentCoordinator",
    "AgentState",
    "CorpusAgent",
    "EvidenceAgent",
    "FeedbackRoute",
    "QAAgent",
    "VerificationDecision",
    "VerifierAgent",
    "get_agent_manifest",
    "make_agent_event",
]
