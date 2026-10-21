import json
import importlib
import sys
import types

from oceangraph.agents import VerifierAgent


def _load_qa_generator(monkeypatch):
    context = types.ModuleType("oceangraph.pipeline.context")
    context.build_complete_context = lambda *args, **kwargs: {}
    monkeypatch.setitem(sys.modules, "oceangraph.pipeline.context", context)
    return importlib.import_module("oceangraph.pipeline.qa_generator")


def _chunks():
    return [
        {
            "file_name": "argo",
            "chunk_id": "1",
            "content": "Float A measured a salinity anomaly in the South China Sea.",
        },
        {
            "file_name": "current",
            "chunk_id": "2",
            "content": "The anomaly was transported by the Kuroshio intrusion.",
        },
        {
            "file_name": "background",
            "chunk_id": "3",
            "content": "Background material not required for this answer.",
        },
    ]


def test_cost_efficient_verifier_uses_one_api_call_and_maps_chunk_positions(monkeypatch):
    qa_generator = _load_qa_generator(monkeypatch)
    calls = []

    def fake_call(prompt, chunks, **kwargs):
        calls.append((prompt, chunks, kwargs))
        return json.dumps(
            {
                "verdict": "ACCEPT",
                "question_standalone": True,
                "single_target": True,
                "answer_supported": True,
                "requires_content": True,
                "supporting_chunks": [1, 2],
                "reason": "Two chunks form the bridge.",
            }
        )

    monkeypatch.setattr(qa_generator, "call_ai_service", fake_call)
    result = qa_generator.verify_qa_cost_efficient(
        _chunks(),
        {
            "question": (
                "Which current transported the salinity anomaly measured by Float A "
                "in the South China Sea?"
            ),
            "answer": "Kuroshio intrusion",
            "short_answers": ["Kuroshio intrusion"],
        },
        "Ocean scientist",
        "Physical oceanography",
        min_supporting_chunks=2,
        max_verification_chunks=3,
    )

    assert len(calls) == 1
    assert calls[0][2]["stage"] == "verification"
    assert result["passes"] is True
    assert result["verification_api_calls"] == 1
    assert result["supporting_chunks"] == ["argo:1", "current:2"]


def test_local_standalone_gate_rejects_before_deepseek(monkeypatch):
    qa_generator = _load_qa_generator(monkeypatch)
    def should_not_call(*args, **kwargs):
        raise AssertionError("DeepSeek must not be called for deterministic failures")

    monkeypatch.setattr(qa_generator, "verify_qa_cost_efficient", should_not_call)
    verifier = VerifierAgent(
        strict_multihop=True,
        min_supporting_chunks=2,
        counterfactual_verification=False,
        verification_mode="balanced",
        max_verification_chunks=3,
        max_unknown_chunks=1,
        verification_profile="cost_efficient",
    )
    decision = verifier.verify(
        _chunks(),
        {
            "question": "According to the provided text, which current was responsible?",
            "answer": "Kuroshio intrusion",
            "short_answers": ["Kuroshio intrusion"],
        },
        {},
        "Ocean scientist",
        "Physical oceanography",
    )

    assert decision.accepted is False
    assert decision.quality_violations == ["question_not_standalone"]
    assert decision.multihop_necessity_result["verification_api_calls"] == 0


def _bibliographic_chunk():
    return {"file_name": "deposit", "chunk_id": "meta", "content": (
        '---\ndocument_id: "deposit-123"\ntitle: "CSIRO Mk3L COAL"\n'
        'publication_year: 2019\nsource: Zenodo\n---'
    )}


def test_metadata_year_shortcut_is_rejected_before_paid_verification(monkeypatch):
    qa_generator = _load_qa_generator(monkeypatch)
    calls = []
    def accepted(*args, **kwargs):
        calls.append(1)
        return json.dumps({"verdict": "ACCEPT", "question_standalone": True,
            "single_target": True, "answer_supported": True,
            "requires_content": True, "supporting_chunks": [1, 2]})
    monkeypatch.setattr(qa_generator, "call_ai_service", accepted)
    result = qa_generator.verify_qa_cost_efficient(
        [_chunks()[0], _bibliographic_chunk()],
        {"question": "In what year was the Zenodo deposit for CSIRO Mk3L COAL published?",
         "answer": "2019"}, "Ocean scientist", "Marine biogeochemistry")
    assert result["passes"] is False
    assert result["verification_api_calls"] == 0
    assert calls == []


def test_metadata_cannot_be_promoted_to_support_even_if_model_accepts(monkeypatch):
    qa_generator = _load_qa_generator(monkeypatch)
    monkeypatch.setattr(qa_generator, "call_ai_service", lambda *a, **kw:
        json.dumps({"verdict": "ACCEPT", "question_standalone": True,
            "single_target": True, "answer_supported": True,
            "requires_content": True, "supporting_chunks": [1, 3]}))
    result = qa_generator.verify_qa_cost_efficient(
        [_chunks()[0], _chunks()[1], _bibliographic_chunk()],
        {"question": "When was the model deposit published?", "answer": "2019"},
        "Ocean scientist", "Marine biogeochemistry")
    assert result["passes"] is False
    assert result["basic_checks_passed"] is False
    assert "deposit:meta" not in result["supporting_chunks"]


def test_mixed_metadata_and_science_body_remains_scientific_evidence():
    from oceangraph.text import is_metadata_only_chunk
    metadata = _bibliographic_chunk()["content"]
    assert is_metadata_only_chunk(metadata) is True
    assert is_metadata_only_chunk(metadata + "\n\nOcean acidification lowers pH.") is False
    assert is_metadata_only_chunk("Ocean acidification lowers pH.") is False


def test_metadata_is_not_scheduled_as_a_qa_seed(monkeypatch):
    from oceangraph import engine
    monkeypatch.setattr(engine, "TEXT_ONLY_MODE", True)
    candidates = engine.filter_chunks_by_qa_type([_bibliographic_chunk(), _chunks()[0]], "multihop")
    assert len(candidates) == 1
    assert candidates[0]["file_name"] == "argo"
