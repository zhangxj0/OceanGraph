import sys
import types

from oceangraph import (
    AGENT_ARCHITECTURE_VERSION,
    AgentCoordinator,
    FRAMEWORK_VERSION,
    CorpusAgent,
    VerifierAgent,
    get_agent_manifest,
)
from oceangraph.agents import VerificationDecision, make_agent_event


def test_v22_exposes_ordered_four_agent_manifest():
    manifest = get_agent_manifest()

    assert FRAMEWORK_VERSION == "4.0.0"
    assert AGENT_ARCHITECTURE_VERSION == "3.0.0"
    assert [agent["agent_id"] for agent in manifest] == [
        "corpus",
        "evidence",
        "qa",
        "verifier",
    ]
    assert manifest[2]["responsibilities"] == [
        "qa_synthesis",
        "subquestion_chaining",
        "reasoning_path_assembly",
    ]
    assert manifest[3]["model_stages"] == ["verification"]


def test_corpus_agent_wraps_existing_validated_operations():
    agent = CorpusAgent()
    chunks = [{"chunk_id": "c1"}]

    assert agent.load_chunks("chunks.json", lambda path: chunks) is chunks
    assert agent.build_index(
        chunks,
        "chunks.json",
        "embeddings",
        lambda rows, path, output: (output, [1.0], [rows[0]["chunk_id"]]),
    ) == ("embeddings", [1.0], ["c1"])


def test_agent_event_is_json_ready_and_uses_stable_actions():
    event = make_agent_event(
        "verifier",
        status="accepted",
        outputs={"atomic": True, "grounded": True, "necessary": True},
    )

    assert event["agent_name"] == "Verifier Agent"
    assert event["actions"] == [
        "atomicity_check",
        "evidence_grounding",
        "multihop_necessity",
    ]
    assert event["outputs"]["necessary"] is True


def test_verifier_agent_owns_the_independent_acceptance_decision(monkeypatch):
    from oceangraph.verification import quality

    qa_generator = types.ModuleType("oceangraph.pipeline.qa_generator")
    qa_generator.verify_qa = (
        lambda *args, **kwargs: "QUESTION_CORRECT ANSWER_CORRECT REQUIRES_CONTENT"
    )
    qa_generator.verify_multihop_necessity = lambda *args, **kwargs: {
        "status": "PASS",
        "necessary_chunks": ["c1", "c2"],
    }
    qa_generator.verify_qa_cost_efficient = lambda *args, **kwargs: {}
    qa_generator.is_verification_successful = lambda *args, **kwargs: True
    qa_generator.is_multihop_necessity_successful = (
        lambda result: result["status"] == "PASS"
    )
    evidence_graph = types.ModuleType("oceangraph.pipeline.evidence_graph")
    evidence_graph.build_evidence_graph = lambda *args, **kwargs: {
        "nodes": [{"id": "c1"}],
        "edges": [],
    }
    monkeypatch.setitem(
        sys.modules, "oceangraph.pipeline.qa_generator", qa_generator
    )
    monkeypatch.setitem(
        sys.modules, "oceangraph.pipeline.evidence_graph", evidence_graph
    )
    monkeypatch.setattr(
        quality, "atomic_qa_violations", lambda *args, **kwargs: []
    )

    verifier = VerifierAgent(
        strict_multihop=True,
        min_supporting_chunks=2,
        counterfactual_verification=False,
        verification_mode="balanced",
        max_verification_chunks=4,
        max_unknown_chunks=1,
    )
    decision = verifier.verify(
        [{"chunk_id": "c1"}, {"chunk_id": "c2"}],
        {
            "question": "Which process links A to B?",
            "answer": "Process C.",
            "short_answers": ["Process C"],
        },
        {},
        "Ocean scientist",
        "Ocean science",
    )

    assert decision.accepted is True
    assert decision.trace_event()["outputs"] == {
        "atomic": True,
        "grounded": True,
        "necessary": True,
        "auditable": True,
        "quality_violations": [],
        "multihop_status": "PASS",
    }


def _decision(*, accepted=False, status="SHORTCUT_FOUND", uncertain=False):
    return VerificationDecision(
        verification_result="verification",
        multihop_necessity_result={"status": status, "passes": accepted},
        evidence_graph={"nodes": [{"id": "c1"}], "edges": []},
        quality_violations=[] if accepted else ["not_atomic"],
        verification_passed=accepted,
        multihop_passed=accepted,
        verifier_uncertain=uncertain,
    )


def test_coordinator_records_stateful_verifier_to_qa_feedback():
    coordinator = AgentCoordinator(max_qa_revisions=1, max_evidence_retries=1)
    state = coordinator.start_candidate(
        seed_chunk_id="c1",
        candidate_id="qa-1",
        base_events=[make_agent_event("corpus", status="completed")],
    )
    coordinator.record_qa(state, make_agent_event("qa", status="completed"))

    route = coordinator.review(state, _decision())

    assert route.target == "qa"
    assert route.action == "revise_candidate"
    assert state.qa_revision_count == 1
    assert state.status == "awaiting_qa_revision"
    assert state.messages == [
        {
            "sequence": 1,
            "source": "verifier",
            "target": "qa",
            "type": "verification_feedback",
            "reason": "SHORTCUT_FOUND",
            "payload": {
                "multihop_status": "SHORTCUT_FOUND",
                "quality_violations": ["not_atomic"],
            },
        }
    ]
    assert state.agent_trace[-1]["outputs"]["feedback_target"] == "qa"


def test_coordinator_routes_insufficient_context_back_to_evidence_agent():
    coordinator = AgentCoordinator(max_qa_revisions=1, max_evidence_retries=1)
    state = coordinator.start_candidate(seed_chunk_id="c1", candidate_id="qa-1")

    route = coordinator.review(
        state,
        _decision(status="INSUFFICIENT_CHUNKS"),
    )

    assert route.target == "evidence"
    assert route.action == "expand_evidence"
    assert state.evidence_retry_count == 1
    assert state.messages[0]["target"] == "evidence"


def test_coordinator_stops_when_revision_budget_is_exhausted():
    coordinator = AgentCoordinator(max_qa_revisions=0, max_evidence_retries=0)
    state = coordinator.start_candidate(seed_chunk_id="c1", candidate_id="qa-1")

    route = coordinator.review(state, _decision())

    assert route.target == "final"
    assert route.action == "reject"
    assert state.status == "rejected"
