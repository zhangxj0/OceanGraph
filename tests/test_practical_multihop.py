"""Offline checks for multi-hop QA without mandatory chain annotations."""
import importlib
import json
import sys
import types
from copy import deepcopy
from pathlib import Path

import pytest

from oceangraph.agents import QAAgent, VerifierAgent
from oceangraph.training import export_training_dataset, validate_training_record


def _generator(monkeypatch):
    context = types.ModuleType("oceangraph.pipeline.context")
    context.build_complete_context = lambda *a, **kw: {}
    monkeypatch.setitem(sys.modules, "oceangraph.pipeline.context", context)
    return importlib.import_module("oceangraph.pipeline.qa_generator")


def _chunks():
    return [
        {"file_name": "float", "chunk_id": "1", "content": "Float A detected anomaly S in the South China Sea."},
        {"file_name": "current", "chunk_id": "2", "content": "Anomaly S was transported by the Kuroshio intrusion."},
    ]


def _qa():
    return {"question": "Which current transported the anomaly detected by Float A in the South China Sea?",
            "answer": "Kuroshio intrusion", "short_answers": ["Kuroshio intrusion"],
            "answer_type": "entity", "question_type": "bridge", "relevance_score": 9,
            "difficulty_score": 6}


def _verdict():
    return {"verdict": "ACCEPT", "question_standalone": True, "single_target": True,
            "answer_supported": True, "multihop_plausible": True,
            "domain_relevant": True, "reason": "Identify anomaly S, then resolve its transporting current."}


def _agent():
    return VerifierAgent(strict_multihop=False, min_supporting_chunks=2,
        counterfactual_verification=False, verification_mode="balanced",
        max_verification_chunks=4, max_unknown_chunks=1,
        verification_profile="practical_multihop")


def test_generation_keeps_multihop_but_accepts_missing_annotations(monkeypatch):
    generator = _generator(monkeypatch)
    calls = []
    def fake(prompt, chunks, **kw):
        calls.append(prompt)
        return json.dumps({"qa_pairs": [_qa()]})
    monkeypatch.setattr(generator, "call_ai_service", fake)
    pairs, _ = QAAgent().generate(_chunks(), "Ocean scientist", "Ocean science",
                                  verification_profile="practical_multihop")
    assert len(pairs) == 1
    assert pairs[0]["supporting_facts"] == []
    assert pairs[0]["evidence_spans"] == []
    assert "at least two linked facts" in calls[0]
    assert "optional" in calls[0]
    assert "If a question can be answered by a single chunk, it is invalid" not in calls[0]


def test_one_pass_accepts_plausible_multihop_without_evidence_ids(monkeypatch):
    generator = _generator(monkeypatch)
    calls = []
    def fake(prompt, chunks, **kw):
        calls.append((prompt, chunks, kw))
        return json.dumps(_verdict())
    monkeypatch.setattr(generator, "call_ai_service", fake)
    def forbidden(*a, **kw):
        pytest.fail("per-chunk necessity verification must not run")
    monkeypatch.setattr(generator, "verify_multihop_necessity", forbidden)
    decision = _agent().verify(_chunks(), _qa(), {}, "Ocean scientist", "Ocean science")
    assert decision.accepted is True
    result = decision.multihop_necessity_result
    assert result["status"] == "MULTIHOP_PLAUSIBLE"
    assert result["necessity_verified"] is False
    assert result["supporting_chunks"] == []
    assert result["verification_api_calls"] == 1
    assert len(calls) == 1
    assert calls[0][2]["stage"] == "verification"


def test_verifier_checks_late_context_facts_without_annotations(monkeypatch):
    generator = _generator(monkeypatch)
    chunks = _chunks()[:1] + [
        {"file_name": f"background_{i}", "chunk_id": "1", "content": "Unrelated ocean background."}
        for i in range(4)
    ] + _chunks()[1:]
    seen = []
    def fake(prompt, supplied, **kw):
        seen.extend(supplied)
        return json.dumps(_verdict())
    monkeypatch.setattr(generator, "call_ai_service", fake)
    assert _agent().verify(chunks, _qa(), {}, "Ocean scientist", "Ocean science").accepted
    assert seen == chunks


def test_practical_trace_does_not_claim_necessity_proof(monkeypatch):
    generator = _generator(monkeypatch)
    monkeypatch.setattr(generator, "call_ai_service", lambda *a, **kw: json.dumps(_verdict()))
    decision = _agent().verify(_chunks(), _qa(), {}, "Ocean scientist", "Ocean science")
    outputs = decision.trace_event()["outputs"]
    assert outputs["necessary"] is False
    assert outputs["multihop_plausible"] is True


def test_verified_annotation_free_candidate_reaches_training_export(monkeypatch, tmp_path):
    generator = _generator(monkeypatch)
    def fake(prompt, chunks, **kw):
        return json.dumps({"qa_pairs": [_qa()]} if kw["stage"] == "generation" else _verdict())
    monkeypatch.setattr(generator, "call_ai_service", fake)
    pairs, metadata = QAAgent().generate(_chunks(), "Ocean scientist", "Ocean science",
                                        verification_profile="practical_multihop")
    decision = _agent().verify(_chunks(), pairs[0], metadata, "Ocean scientist", "Ocean science")
    item = {**pairs[0], "context_chunks": _chunks(), "evidence_graph": decision.evidence_graph,
            "multihop_necessity_result": decision.multihop_necessity_result}
    manifest = export_training_dataset([item], _chunks(), tmp_path, split="train")
    assert manifest["exported_records"] == 1


@pytest.mark.parametrize("field,value", [
    ("multihop_plausible", False), ("answer_supported", False),
    ("question_standalone", False), ("single_target", False),
    ("domain_relevant", False), ("verdict", "REJECT"),
    ("multihop_plausible", "false"), ("answer_supported", None),
])
def test_relaxed_verification_still_rejects_failed_checks(monkeypatch, field, value):
    generator = _generator(monkeypatch)
    payload = _verdict()
    payload[field] = value
    monkeypatch.setattr(generator, "call_ai_service", lambda *a, **kw: json.dumps(payload))
    assert _agent().verify(_chunks(), _qa(), {}, "Ocean scientist", "Ocean science").accepted is False


@pytest.mark.parametrize("payload", [{}, {"verdict": "ACCEPT"}, "not json"])
def test_missing_verifier_checks_fail_closed(monkeypatch, payload):
    generator = _generator(monkeypatch)
    monkeypatch.setattr(generator, "call_ai_service", lambda *a, **kw: json.dumps(payload))
    assert _agent().verify(_chunks(), _qa(), {}, "Ocean scientist", "Ocean science").accepted is False


def test_redundant_or_same_chunk_facts_are_not_automatically_rejected(monkeypatch):
    generator = _generator(monkeypatch)
    monkeypatch.setattr(generator, "call_ai_service", lambda *a, **kw: json.dumps(_verdict()))
    combined = dict(_chunks()[0], content=" ".join(chunk["content"] for chunk in _chunks()))
    assert _agent().verify([combined], _qa(), {}, "Ocean scientist", "Ocean science").accepted is True


def test_metadata_only_context_is_rejected_without_api(monkeypatch):
    generator = _generator(monkeypatch)
    monkeypatch.setattr(generator, "call_ai_service", lambda *a, **kw: pytest.fail("no body to verify"))
    metadata = {"file_name": "deposit", "chunk_id": "1",
                "content": "---\ndocument_id: 123\nsource: Zenodo\npublication_year: 2019\n---"}
    decision = _agent().verify([metadata], _qa(), {}, "Ocean scientist", "Ocean science")
    assert decision.accepted is False
    assert decision.multihop_necessity_result["verification_api_calls"] == 0


def _accepted_record():
    return {**_qa(), "context_chunks": _chunks(),
            "multihop_necessity_result": {**_verdict(), "passes": True,
                "basic_checks_passed": True, "verification_profile": "practical_multihop",
                "status": "MULTIHOP_PLAUSIBLE", "necessity_verified": False}}


def test_training_accepts_verified_record_without_graph_or_agent_trace():
    assert validate_training_record(_accepted_record()) == []


@pytest.mark.parametrize("field", ["passes", "answer_supported", "multihop_plausible", "domain_relevant"])
def test_training_keeps_verification_requirements(field):
    item = _accepted_record()
    item["multihop_necessity_result"][field] = False
    assert validate_training_record(item)


def test_compact_export_uses_context_for_sources_without_chain_annotations(tmp_path):
    item = _accepted_record()
    manifest = export_training_dataset([item], _chunks(), tmp_path, split="train")
    assert manifest["exported_records"] == 1
    row = json.loads((tmp_path / "train.jsonl").read_text(encoding="utf-8"))
    assert row["question"] == item["question"]
    assert row["answer"] == item["answer"]
    assert row["verification"]["profile"] == "practical_multihop"
    assert row["verification"]["necessity_verified"] is False
    assert row["metadata"]["source_documents"] == ["float", "current"]
    for auxiliary in ("evidence", "reasoning", "retrieval", "multi_agent", "hop_count"):
        assert auxiliary not in row


def test_optional_graph_does_not_override_source_context(tmp_path):
    item = _accepted_record()
    item["evidence_graph"] = {"supporting_chunk_ids": ["hallucinated:99"]}
    manifest = export_training_dataset([item], _chunks(), tmp_path, split="train")
    assert manifest["exported_records"] == 1


def test_shared_source_context_stays_in_same_split_without_graph(tmp_path):
    first, second = _accepted_record(), deepcopy(_accepted_record())
    second["question"] = "Which current carried anomaly S?"
    manifest = export_training_dataset([first, second], _chunks(), tmp_path)
    assert manifest["exported_records"] == 2
    assert manifest["source_component_count"] == 1
    assert manifest["source_leakage_detected"] is False


def test_unresolvable_context_is_not_exported_as_searchable(tmp_path):
    manifest = export_training_dataset([_accepted_record()], _chunks()[:1], tmp_path)
    assert manifest["exported_records"] == 0


def test_runtime_accepts_profile_and_distinguishes_checkpoint_fingerprint(monkeypatch):
    from oceangraph import engine
    monkeypatch.delenv("OCEANGRAPH_VERIFICATION_PROFILE", raising=False)
    runtime = engine.apply_runtime_config({"qa_generation": {
        "type": "multihop", "strict_multihop_verification": False,
        "verification_profile": "practical_multihop"}})
    assert runtime["qa_generation"]["verification_profile"] == "practical_multihop"
    assert runtime["qa_generation"]["type"] == "multihop"


def test_practical_selection_does_not_apply_strict_model_screen(monkeypatch):
    generator = _generator(monkeypatch)
    monkeypatch.setattr(generator, "call_ai_service", lambda *a, **kw: pytest.fail("one final review is sufficient"))
    selected, rejected = QAAgent().select([_qa()], _chunks(), "Ocean scientist", "Ocean science",
        use_model_review=True, verification_profile="practical_multihop")
    assert len(selected) == 1
    assert rejected == []


def test_engine_seed_preserves_global_id_through_context_and_export(monkeypatch, tmp_path):
    generator = _generator(monkeypatch)
    spec = importlib.util.spec_from_file_location("practical_context_test",
        Path(__file__).parents[1] / "src/oceangraph/pipeline/context.py")
    context = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, context)
    spec.loader.exec_module(context)
    monkeypatch.setitem(sys.modules, "oceangraph.pipeline.context", context)
    monkeypatch.setattr(context, "call_vlm_interweaved", lambda *a, **kw: pytest.fail("depth zero must be offline"))
    from oceangraph import engine
    for name, value in {"QA_VERIFICATION_PROFILE": "practical_multihop", "QA_STRICT_MULTIHOP": False,
                        "QA_MODEL_SELECTION": False, "QA_CORRECTION_ENABLED": False, "MAX_DEPTH": 0}.items():
        monkeypatch.setattr(engine, name, value)
    monkeypatch.setattr(generator, "call_ai_service", lambda *a, **kw:
        json.dumps({"qa_pairs": [_qa()]} if kw["stage"] == "generation" else _verdict()))
    seed = {**_chunks()[0], "global_chunk_id": "chunk_42",
            "content": " ".join(c["content"] for c in _chunks())}
    accepted, failed, _ = engine.process_single_chunk_for_qa((0, seed), "Ocean science", "Ocean scientist")
    assert failed == []
    assert len(accepted) == 1
    assert accepted[0]["context_chunks"][0].get("global_chunk_id") == "chunk_42"
    manifest = export_training_dataset(accepted, [seed], tmp_path, split="train")
    assert manifest["exported_records"] == 1
