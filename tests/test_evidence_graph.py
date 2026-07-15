from mirage.pipeline.evidence_graph import build_evidence_graph, build_search_trajectory


def test_evidence_graph_uses_counterfactually_necessary_chunks():
    chunks = [
        {"file_name": "physical", "chunk_id": "1", "content": "Cold water sinks carbon."},
        {"file_name": "biology", "chunk_id": "2", "content": "Particles export carbon."},
        {"file_name": "background", "chunk_id": "3", "content": "The ocean stores carbon."},
    ]
    graph = build_evidence_graph(
        chunks,
        necessity_result={
            "necessary_chunks": ["physical:1", "biology:2"],
            "redundant_chunks": ["background:3"],
        },
    )

    assert graph["construction"] == "counterfactual_minimal_evidence_graph"
    assert graph["supporting_chunk_ids"] == ["physical:1", "biology:2"]
    bridge_edges = [edge for edge in graph["edges"] if edge["type"] == "multi_hop_bridge"]
    assert bridge_edges == [
        {
            "source": "physical:1",
            "target": "biology:2",
            "type": "multi_hop_bridge",
            "weight": 1.0,
        }
    ]


def test_search_trajectory_preserves_rank_action_and_termination():
    trajectory = build_search_trajectory(
        {
            "status": "COMPLETE",
            "termination_reason": "Context verified as complete",
            "iteration_logs": [
                {
                    "depth": 1,
                    "search_strings": ["ocean carbon"],
                    "model_route": {"profile": "generator", "model": "qwen3.7-plus"},
                    "retrieved_chunks": [
                        {
                            "search_query": "ocean carbon",
                            "chunk_id": "2",
                            "file_name": "biology",
                            "score": 0.8,
                            "rank": 1,
                            "verdict": "EXPLANATORY",
                            "reason": "Adds the missing mechanism",
                        }
                    ],
                }
            ],
        }
    )

    assert trajectory[0]["retrieved"][0]["rank"] == 1
    assert trajectory[0]["retrieved"][0]["action"] == "select"
    assert trajectory[0]["termination"]["status"] == "COMPLETE"
