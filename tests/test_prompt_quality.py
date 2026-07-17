from pathlib import Path

from oceangraph.core.prompts import PROMPTS
from oceangraph.verification.quality import (
    atomic_qa_violations,
    has_visible_self_correction,
    is_atomic_short_answer_qa,
)


def test_generation_prompt_forbids_visible_self_correction():
    prompt = PROMPTS["question_answer_generation"]

    assert "Perform calculations and reconsiderations silently" in prompt
    assert "Atomic Question Requirement" in prompt
    assert "exactly ONE final unknown" in prompt
    assert "Single Canonical Short Answer" in prompt
    assert "Every prerequisite used by the answer" in prompt


def test_selection_accepts_unique_entities_without_document_title():
    prompt = PROMPTS["question_answer_selection"]

    assert "water parcel WP-27" in prompt
    assert "A document-title citation is optional" in prompt


def test_consolidated_verifier_is_single_pass_and_fair_to_bridge_evidence():
    prompt = PROMPTS["consolidated_multihop_check"]

    assert "INDEPENDENTLY" in prompt
    assert "genuine single-chunk shortcut" in prompt
    assert "bridge fact" in prompt
    assert "Do not penalize irrelevant background chunks" in prompt
    assert '"single_chunk_checks"' in prompt


def test_visible_self_correction_is_detected_deterministically():
    answer = "The band is CB-H. Wait, 35.06 is below 35.10, so it is CB-L."

    assert has_visible_self_correction(answer)
    assert not has_visible_self_correction("The corrected salinity is 35.06 PSU, so the band is CB-L.")


def test_verification_and_correction_apply_deterministic_gate():
    root = Path(__file__).parents[1]
    generator = (root / "src/oceangraph/pipeline/qa_generator.py").read_text(encoding="utf-8")
    engine = (root / "src/oceangraph/engine.py").read_text(encoding="utf-8")

    assert "if answer and has_visible_self_correction(answer):" in generator
    assert "atomic_qa_violations(question, answer, short_answers)" in generator
    assert "Answer contains visible drafting or self-correction." in engine
    assert "Atomic QA quality gate failed:" in engine
    assert '"supporting_facts",' in generator
    assert "**get_structured_qa_fields(f.get('original_qa', {}))" in engine
    assert "optional model selection disabled" in generator
    assert '"method": "consolidated_single_pass"' in generator
    assert "verification_api_calls" in generator
    assert "use_model_review=QA_MODEL_SELECTION" in engine


def test_real_compound_samples_are_rejected_as_non_atomic():
    first_question = (
        "2024 年 S&P Global 营收增长 15%、任命 Eric Aboaf 为 CFO；同期收购了"
        "哪家公司以增强共识估算？通过分红和回购共向股东返还多少？"
    )
    first_answer = "收购了 Visible Alpha；向股东返还共 $4.4 billion。"
    second_question = (
        "董事会在完成哪笔重大收购后选举 Martina Cheung 为 CEO？"
        "她随后组建了哪个新团队以确保客户了解 S&P Global 的完整能力？"
    )
    second_answer = "在完成 IHS Markit 整合后选举 Martina Cheung；她组建了 Chief Client Office。"

    first_violations = atomic_qa_violations(
        first_question,
        first_answer,
        ["Visible Alpha", "$4.4 billion"],
    )
    second_violations = atomic_qa_violations(
        second_question,
        second_answer,
        ["IHS Markit", "Chief Client Office"],
    )

    assert "multiple_question_marks" in first_violations
    assert "multiple_answer_targets" in first_violations
    assert "short_answer_count_not_one" in first_violations
    assert "multiple_question_marks" in second_violations
    assert "multiple_answer_targets" in second_violations


def test_atomic_bridge_questions_with_minimal_answers_are_accepted():
    assert is_atomic_short_answer_qa(
        "2024 年营收增长 15% 且任命 Eric Aboaf 为 CFO 的公司，同期收购了哪家公司以增强共识估算能力？",
        "Visible Alpha",
        ["Visible Alpha"],
    )
    assert is_atomic_short_answer_qa(
        "完成 IHS Markit 整合后任命 Martina Cheung 为 CEO 的公司，她随后组建了哪个新团队？",
        "Chief Client Office",
        ["Chief Client Office"],
    )


def test_answer_must_equal_the_single_canonical_short_answer():
    violations = atomic_qa_violations(
        "任命 Eric Aboaf 为 CFO 的公司收购了哪家公司？",
        "该公司收购了 Visible Alpha。",
        ["Visible Alpha"],
    )

    assert "answer_not_canonical_short_answer" in violations
