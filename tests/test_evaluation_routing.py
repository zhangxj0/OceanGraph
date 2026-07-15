from pathlib import Path

import yaml

from oceangraph.evaluation import metrics


def test_evaluation_calls_are_bound_to_verification_route():
    assert metrics.call_llm.keywords["stage"] == "verification"
    assert metrics.batch_call_llm.keywords["stage"] == "verification"
    assert metrics.call_vlm_interweaved.keywords["stage"] == "verification"
    assert metrics.batch_call_vlm_interweaved.keywords["stage"] == "verification"


def test_evaluation_uses_local_bge_without_legacy_frameworks():
    root = Path(__file__).parents[1]
    source = (root / "src" / "oceangraph" / "evaluation" / "metrics.py").read_text(
        encoding="utf-8"
    ).lower()
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8").lower()
    config = yaml.safe_load(
        (root / "configs" / "oceangraph.yaml.example").read_text(encoding="utf-8")
    )

    assert "google.generativeai" not in source
    assert "langchain_google_genai" not in source
    assert "ragas" not in source
    assert "ragas" not in pyproject
    assert "langchain" not in pyproject
    assert "google-generativeai" not in pyproject
    assert config["evaluation"]["judge_stage"] == "verification"
    assert config["evaluation"]["embedding_model"] == "BAAI/bge-m3"


def test_prepare_qa_parses_structured_delimiter_response(monkeypatch):
    response = """<|#|>START<|#|>
ConceptHops<|#|>Pressure --> Density --> Depth<|#|>
Answer Claims<|#|>- Pressure increases with depth
- Density affects the pressure gradient<|#|>
Reference Claims<|#|>- Pressure increases with depth<|#|>
Reverse Questions<|#|>- How does pressure change with depth?<|#|>
- What controls the pressure gradient?<|#|>END<|#|>"""
    monkeypatch.setattr(metrics, "call_llm", lambda prompt: response)
    evaluator = metrics.RoutedMetricsEvaluator.__new__(metrics.RoutedMetricsEvaluator)
    evaluator.num_reverse_questions = 3

    prepared = evaluator.prepare_qa(
        "How do density and depth affect pressure?",
        "Pressure increases with depth according to density.",
        "Pressure increases with depth.",
        ["Ocean pressure context"],
    )

    assert prepared.concept_hops_question == "Pressure --> Density --> Depth"
    assert prepared.answer_claims == [
        "Pressure increases with depth",
        "Density affects the pressure gradient",
    ]
    assert prepared.reference_claims == ["Pressure increases with depth"]
    assert prepared.reverse_questions == [
        "How does pressure change with depth?",
        "What controls the pressure gradient?",
    ]


def test_multihop_parser_accepts_structured_delimiter_response(monkeypatch):
    response = (
        "<|#|>START<|#|>Hop Count<|#|>2<|#|>Reasoning Score<|#|>0.85"
        "<|#|>Bridge Entity<|#|>thermocline<|#|>Explanation<|#|>Two facts combine."
        "<|#|>END<|#|>"
    )
    monkeypatch.setattr(metrics, "batch_call_llm", lambda prompts, **kwargs: [response])
    evaluator = metrics.RoutedMetricsEvaluator.__new__(metrics.RoutedMetricsEvaluator)

    result = evaluator.batch_evaluate_multihop_reasoning([
        {"question": "Q", "answer": "A", "contexts": ["C1", "C2"]}
    ])[0]

    assert result == {
        "hop_count": 2,
        "reasoning_score": 0.85,
        "bridge_entity": "thermocline",
    }


def test_context_necessity_parses_status_field(monkeypatch):
    responses = iter([
        "<|#|>START<|#|>Answer<|#|>A guess<|#|>END<|#|>",
        "<|#|>START<|#|>Status<|#|>PARTIAL<|#|>END<|#|>",
    ])
    monkeypatch.setattr(metrics, "call_llm", lambda prompt: next(responses))
    evaluator = metrics.RoutedMetricsEvaluator.__new__(metrics.RoutedMetricsEvaluator)

    result = evaluator.evaluate_context_necessity("Q", "A", "C")

    assert result["context_necessity_score"] == 0.5
    assert result["without_context_correct"] is False
