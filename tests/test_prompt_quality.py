from pathlib import Path

from oceangraph.core.prompts import PROMPTS
from oceangraph.verification.quality import has_visible_self_correction


def test_generation_prompt_forbids_visible_self_correction():
    prompt = PROMPTS["question_answer_generation"]

    assert "Perform calculations and reconsiderations silently" in prompt
    assert "never include drafting language" in prompt
    assert "Every prerequisite used by the answer" in prompt


def test_selection_accepts_unique_entities_without_document_title():
    prompt = PROMPTS["question_answer_selection"]

    assert "water parcel WP-27" in prompt
    assert "A document-title citation is optional" in prompt


def test_visible_self_correction_is_detected_deterministically():
    answer = "The band is CB-H. Wait, 35.06 is below 35.10, so it is CB-L."

    assert has_visible_self_correction(answer)
    assert not has_visible_self_correction("The corrected salinity is 35.06 PSU, so the band is CB-L.")


def test_verification_and_correction_apply_deterministic_gate():
    root = Path(__file__).parents[1]
    generator = (root / "src/oceangraph/pipeline/qa_generator.py").read_text(encoding="utf-8")
    engine = (root / "src/oceangraph/engine.py").read_text(encoding="utf-8")

    assert "if answer and has_visible_self_correction(answer):" in generator
    assert "Answer contains visible drafting or self-correction." in engine
    assert '"supporting_facts",' in generator
    assert "**get_structured_qa_fields(f.get('original_qa', {}))" in engine
