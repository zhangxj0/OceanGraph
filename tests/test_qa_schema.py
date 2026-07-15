import pytest
from pydantic import ValidationError

from oceangraph.schemas import QAResponse


def test_qa_response_coerces_scores_and_validates_evidence():
    response = QAResponse.model_validate(
        {
            "qa_pairs": [
                {
                    "question": "How do the two mechanisms differ?",
                    "answer": "One transports dissolved carbon and one transports particles.",
                    "relevance_score": "9",
                    "difficulty_score": "8",
                    "supporting_facts": [
                        {"chunk": "Chunk 1", "fact": "Dissolved carbon sinks."},
                        {"chunk": "Chunk 2", "fact": "Particles sink."},
                    ],
                    "evidence_spans": [
                        {"chunk": "Chunk 1", "span": "dissolved carbon"},
                        {"chunk": "Chunk 2", "span": "particles"},
                    ],
                }
            ],
            "keywords_per_chunk": {"chunk_1": ["carbon"], "chunk_2": ["particles"]},
            "chunk_count": 2,
        }
    )

    assert response.qa_pairs[0].relevance_score == 9
    assert len(response.qa_pairs[0].supporting_facts) == 2


def test_qa_response_rejects_empty_question():
    with pytest.raises(ValidationError):
        QAResponse.model_validate(
            {"qa_pairs": [{"question": "", "answer": "An answer"}]}
        )
