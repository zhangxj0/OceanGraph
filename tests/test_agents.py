import sys
import types

from oceangraph import (
    AGENT_ARCHITECTURE_VERSION,
    FRAMEWORK_VERSION,
    CorpusAgent,
    VerifierAgent,
    get_agent_manifest,
)
from oceangraph.agents import make_agent_event


def test_v22_exposes_ordered_four_agent_manifest():
    manifest = get_agent_manifest()

    assert FRAMEWORK_VERSION == "2.2.0"
    assert AGENT_ARCHITECTURE_VERSION == "2.2.0"
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
    monkeypatch.setattr(quality, "atomic_qa_violations", lambda *args: [])

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
