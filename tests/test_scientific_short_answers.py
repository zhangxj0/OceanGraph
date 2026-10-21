import pytest

from oceangraph.verification.quality import atomic_qa_violations


@pytest.mark.parametrize('answer', [
    '2.9%', '12.70 microatmospheres', '0.3 to 16.0 degrees C',
    'C. decipiens', 'E. huxleyi', 'S. pistillata',
])
def test_scientific_short_answers_are_not_multiple_sentences(answer):
    assert 'multi_sentence_answer' not in atomic_qa_violations(
        'Which value or organism satisfies the stated condition?', answer, [answer])


@pytest.mark.parametrize('answer', [
    '2.9%. It increased during summer.',
    'C. decipiens. It grew fastest.',
    'Carbon export declined. Temperature rose.',
])
def test_actual_multiple_sentences_are_still_rejected(answer):
    assert 'multi_sentence_answer' in atomic_qa_violations(
        'Which value or organism satisfies the stated condition?', answer, [answer])
