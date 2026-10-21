"""Deterministic, zero-API quality gates for training QA records."""

import re
from typing import Iterable, List, Optional


_VAGUE_CONTEXT_PATTERNS = (
    r"\b(?:the\s+)?(?:provided|given|above|below|aforementioned)\s+"
    r"(?:text|context|document|study|report|figure|table|section|data)\b",
    r"\b(?:this|that|the)\s+(?:figure|table|section|document|study|report)\b",
    r"\b(?:as|like)\s+(?:shown|described|mentioned|reported)\s+"
    r"(?:above|below|in\s+the\s+(?:text|document))\b",
    r"\baccording\s+to\s+(?:the|this)\s+(?:text|document|study|report)\b",
    r"(?:上述|下述|以上|以下|前述|后文|本文|本研究|该研究|该文|文中|"
    r"图中|表中|如图|如下|所述|这项研究|该数据|这些数据)",
)


def has_visible_self_correction(answer: str) -> bool:
    """Detect drafting or self-correction language that invalidates a final answer."""
    if not answer:
        return False
    patterns = [
        r"\bwait\s*[,.:;!?]",
        r"\blet me (?:re-?read|recalculate|re-evaluate|check|correct)\b",
        r"\b(?:recalculation|self-correction|correction)\s*:",
        r"\bi (?:need to|must|should) (?:correct|revise|reconsider)\b",
    ]
    return any(re.search(pattern, answer, re.IGNORECASE) for pattern in patterns)


def standalone_question_violations(question: str) -> List[str]:
    """Detect explicit references that make a question depend on hidden context."""
    normalized = _normalize_text(question)
    if not normalized:
        return ["question_not_standalone"]
    if any(
        re.search(pattern, normalized, re.IGNORECASE)
        for pattern in _VAGUE_CONTEXT_PATTERNS
    ):
        return ["question_not_standalone"]
    return []


def atomic_qa_violations(
    question: str,
    answer: str,
    short_answers: Optional[Iterable[str]] = None,
    *,
    max_answer_words: int = 12,
    max_answer_cjk_chars: int = 16,
) -> List[str]:
    """Return hard failures for one standalone question and one short EM answer."""
    violations: List[str] = []
    normalized_question = _normalize_text(question)
    normalized_answer = _normalize_answer(answer)

    if not normalized_question:
        violations.append("missing_question")
    if not normalized_answer:
        violations.append("missing_answer")
    violations.extend(standalone_question_violations(normalized_question))

    if normalized_question.count("?") + normalized_question.count("？") > 1:
        violations.append("multiple_question_marks")

    chinese_targets = re.findall(
        r"哪(?:一|个|些|种|项)?|什么|何时|哪里|何处|为何|为什么|如何|是否|"
        r"多少|几(?:个|种|项|次)?|谁",
        normalized_question,
    )
    if len(chinese_targets) > 1:
        violations.append("multiple_answer_targets")

    if re.search(
        r"\b(?:and|or)\s+(?:who|what|which|where|when|why|how(?:\s+(?:many|much))?)\b",
        normalized_question,
        re.IGNORECASE,
    ):
        violations.append("compound_interrogative")

    if re.search(r"\brespectively\b|分别|各自", normalized_question, re.IGNORECASE):
        violations.append("multiple_requested_outputs")

    if re.search(r"[;；]", normalized_answer):
        violations.append("multi_clause_answer")
    elif re.search(
        r"，\s*(?:并且|以及|同时|另外|而且)|,\s+(?:and|while|whereas)\s+",
        normalized_answer,
        re.IGNORECASE,
    ):
        violations.append("multi_clause_answer")

    answer_without_terminal = normalized_answer.rstrip(".!。！")
    # Decimal points and abbreviated scientific genera are not sentence ends.
    sentence_text = re.sub(r"(?<=\d)\.(?=\d)", "", answer_without_terminal)
    sentence_text = re.sub(r"\b[A-Z]\.(?=\s+[a-z])", "", sentence_text)
    if re.search(r"[.!。！]\s*\S", sentence_text):
        violations.append("multi_sentence_answer")

    latin_words = re.findall(r"\b[\w$%+./-]+\b", normalized_answer, re.UNICODE)
    cjk_chars = re.findall(r"[\u3400-\u9fff]", normalized_answer)
    if len(latin_words) > max_answer_words or len(cjk_chars) > max_answer_cjk_chars:
        violations.append("answer_too_long")

    if short_answers is not None:
        canonical_answers = [
            _normalize_answer(item)
            for item in short_answers
            if _normalize_answer(item)
        ]
        if len(canonical_answers) != 1:
            violations.append("short_answer_count_not_one")
        elif _answer_key(canonical_answers[0]) != _answer_key(normalized_answer):
            violations.append("answer_not_canonical_short_answer")

    return list(dict.fromkeys(violations))


def is_atomic_short_answer_qa(
    question: str,
    answer: str,
    short_answers: Optional[Iterable[str]] = None,
) -> bool:
    """Return whether one question asks for one minimal final answer."""
    return not atomic_qa_violations(question, answer, short_answers)


def _normalize_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_answer(value: object) -> str:
    return _normalize_text(value).strip(" \"'`.,;:!?。；：！？")


def _answer_key(value: str) -> str:
    return re.sub(r"\s+", " ", value).casefold()
