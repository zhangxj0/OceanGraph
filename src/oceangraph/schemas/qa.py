"""Pydantic contracts for generated QA records."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SupportingFact(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    chunk: str
    fact: str


class EvidenceSpan(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    chunk: str
    span: str


class AgentTraceEvent(BaseModel):
    """Per-record provenance emitted by one v3.0 runtime agent."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    agent_id: str
    agent_name: str
    status: str
    actions: List[str] = Field(default_factory=list)
    outputs: Dict[str, Any] = Field(default_factory=dict)


class QAPair(BaseModel):
    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    schema_version: str = "oceangraph.qa.v3.0.0"
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    short_answers: List[str] = Field(default_factory=list)
    relevance_score: int = 0
    difficulty_score: int = 0
    question_type: str = "multihop"
    answer_type: str = ""
    subdomain: str = ""
    hop_count: int = Field(default=0, ge=0)
    declared_hop_count: int | None = Field(default=None, ge=0)
    retrieval_hop_count: int = Field(default=0, ge=0)
    context_chunk_count: int = Field(default=0, ge=0)
    taxonomy_version: str = "3.0.0"
    sub_questions: List[str] = Field(default_factory=list)
    reasoning_path: str = ""
    supporting_facts: List[SupportingFact] = Field(default_factory=list)
    evidence_spans: List[EvidenceSpan] = Field(default_factory=list)
    agent_trace: List[AgentTraceEvent] = Field(default_factory=list)
    coordination_trace: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("short_answers", "sub_questions", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: Any) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value) if isinstance(value, (list, tuple)) else []


class QAResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    qa_pairs: List[QAPair] = Field(default_factory=list)
    keywords_per_chunk: Dict[str, List[str]] = Field(default_factory=dict)
    related_keywords: str = ""
    chunk_count: int = 0
