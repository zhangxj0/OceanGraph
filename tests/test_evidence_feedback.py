import sys
import types

from oceangraph.agents import EvidenceAgent


def test_evidence_agent_expands_context_from_verifier_feedback(monkeypatch):
    context_module = types.ModuleType("oceangraph.pipeline.context")
    context_module.retrieve_chunks_for_query = lambda query, top_k: [
            {
                "content": "Complementary evidence.",
                "chunk_id": "c2",
                "file_name": "doc-b",
                "score": 0.9,
            }
        ]
    monkeypatch.setitem(
        sys.modules,
        "oceangraph.pipeline.context",
        context_module,
    )
    initial = {
        "status": "INCOMPLETE",
        "depth": 1,
        "hop_count": 0,
        "chunks": [
            {"content": "Seed evidence.", "chunk_id": "c1", "file_name": "doc-a"}
        ],
        "chunks_added": [{"chunk_id": "c1", "file_name": "doc-a"}],
        "search_history": [],
        "iteration_logs": [],
    }

    expanded = EvidenceAgent().expand_context_from_feedback(
        initial,
        query="Which evidence bridges A and B?",
        top_k=2,
    )

    assert expanded["status"] == "EXPANDED_FROM_VERIFIER"
    assert [chunk["chunk_id"] for chunk in expanded["chunks"]] == ["c1", "c2"]
    assert expanded["feedback_chunks_added"] == 1
    assert expanded["hop_count"] == 2
    assert expanded["retrieval_hop_count"] == 1
    assert expanded["context_chunk_count"] == 2
    assert expanded["iteration_logs"][-1]["source"] == "verifier_feedback"
    assert initial["chunks"] == [
        {"content": "Seed evidence.", "chunk_id": "c1", "file_name": "doc-a"}
    ]
