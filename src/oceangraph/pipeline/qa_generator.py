#!/usr/bin/env python3
"""
QA Generation from Multi-hop Context Completion

Pipeline for each chunk:
1. Load chunk from INPUT_CHUNKS_FILE
2. Build multihop context using retrieval (adds related chunks)
3. Generate Q&A pairs from the complete multihop context
4. Select best Q&A pairs using selection agent
5. Verify Q&A pairs require the context to answer
6. Save successful and failed Q&A pairs
"""

import json
import re
import logging
import os
from typing import Any, Dict, List, Tuple
from pydantic import ValidationError
from tqdm import tqdm
from oceangraph.core.llm import call_vlm_interweaved, setup_logging, batch_call_vlm_interweaved
from oceangraph.pipeline.context import build_complete_context
from oceangraph.pipeline.domain import fetch_domain_and_role, load_domain_expert_from_env, save_domain_expert_to_env
from oceangraph.pipeline.evidence_graph import (
    build_evidence_graph,
    build_search_trajectory,
    ensure_short_answers,
)
from oceangraph.core.prompts import PROMPTS, PROMPTS_CHUNK
from oceangraph.schemas import QAResponse
from oceangraph.verification import (
    evaluate_multihop_gate,
    parse_consolidated_multihop_response,
    prioritize_verification_chunks,
)
from oceangraph.verification.quality import (
    atomic_qa_violations,
    has_visible_self_correction,
)

# Configuration (override via config.yaml or command line)
INPUT_CHUNKS_FILE = "output/results/chunks.json"
OUTPUT_SUCCESSFUL = "qa_multihop_pass.json"
OUTPUT_FAILED = "qa_multihop_fail.json"
OUTPUT_IRRELEVANT = "irrelevant_chunk.json"
MAX_CHUNKS = None  # Process all chunks (set to integer for testing, e.g., 100)
CHUNK_ADDITION_MODE = "RELATED"  # EXPLANATORY (only direct answers) or RELATED (both)

def call_ai_service(
    prompt: str,
    chunks: List[Dict],
    stage: str = "default",
    response_format: Dict[str, Any] | None = None,
) -> str:
    """Unified call to VLM using interleaved chunks"""
    return call_vlm_interweaved(
        prompt,
        chunks,
        stage=stage,
        response_format=response_format,
    )


def _as_list(value: Any) -> List:
    """Return value as a list while preserving empty values as []."""
    return value if isinstance(value, list) else []


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_structured_qa_fields(qa_pair: Dict) -> Dict:
    """Return dataset-facing structured fields from a generated QA pair."""
    return {
        "question_type": qa_pair.get("question_type", "multihop"),
        "answer_type": qa_pair.get("answer_type", ""),
        "short_answers": _as_list(qa_pair.get("short_answers")),
        "subdomain": qa_pair.get("subdomain", ""),
        "declared_hop_count": qa_pair.get("hop_count", None),
        "sub_questions": _as_list(qa_pair.get("sub_questions")),
        "reasoning_path": qa_pair.get("reasoning_path", ""),
        "supporting_facts": _as_list(qa_pair.get("supporting_facts")),
        "evidence_spans": _as_list(qa_pair.get("evidence_spans")),
    }


def _extract_json_object(response: str) -> Dict:
    """Extract the first JSON object from an LLM response."""
    if not response:
        return {}

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL | re.IGNORECASE)
    json_text = fenced.group(1) if fenced else None

    if json_text is None:
        start = response.find("{")
        end = response.rfind("}")
        if start == -1 or end <= start:
            return {}
        json_text = response[start:end + 1]

    try:
        parsed = json.loads(json_text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        logging.warning("Could not parse structured QA JSON response")
        return {}


def _parse_json_qa_response(response: str) -> Tuple[List[Dict], Dict]:
    """Parse the preferred structured QA JSON response."""
    data = _extract_json_object(response)
    if not data:
        return [], {}

    try:
        validated = QAResponse.model_validate(data)
    except ValidationError as exc:
        logging.warning("Structured QA response failed schema validation: %s", exc)
        return [], {}

    qa_metadata = {
        "keywords_per_chunk": validated.keywords_per_chunk,
        "related_keywords": validated.related_keywords,
        "chunk_count": validated.chunk_count,
    }
    qa_pairs = []
    for item in validated.qa_pairs:
        record = item.model_dump()
        if not record["hop_count"]:
            record["hop_count"] = validated.chunk_count
        record["relevance_score"] = str(record["relevance_score"])
        record["difficulty_score"] = str(record["difficulty_score"])
        qa_pairs.append(record)
    return qa_pairs, qa_metadata

def check_chunk_relevance(chunk_content: str, expert_persona: str, domain: str) -> bool:
    """Check if a chunk is relevant to the expert role and domain. Returns True if relevant, False otherwise."""
    print(f"Checking chunk relevance for {expert_persona} in {domain}...")
    
    # Format prompt - domain should never be None at this point
    domain_context = domain if domain else "unspecified domain"
    
    prompt = PROMPTS_CHUNK["relevance_check"].format(
        expert_persona=expert_persona,
        domain=domain_context,
        content=chunk_content[:2000]  # Limit content length to avoid token limits
    )
    
    # Use a simple text-only LLM call for relevance check (no images needed)
    from oceangraph.core.llm import call_llm_simple
    response = call_llm_simple(prompt, stage="corpus")
    
    tuple_delimiter = PROMPTS.get("DEFAULT_TUPLE_DELIMITER", "<|#|>")
    
    # Parse new format: <|#|>START<|#|>Status<|#|><RELEVANT | NOT_RELEVANT><|#|>Explanation<|#|><text><|#|>END<|#|>
    is_relevant = False
    if tuple_delimiter in response:
        parts = response.split(tuple_delimiter)
        for i, part in enumerate(parts):
            if part.strip().lower() == "status" and i + 1 < len(parts):
                status_value = parts[i + 1].strip().upper()
                is_relevant = "RELEVANT" in status_value and "NOT_RELEVANT" not in status_value
                break
    else:
        # Fallback: old format - just check for keywords
        response_upper = response.strip().upper()
        is_relevant = "RELEVANT" in response_upper and "NOT_RELEVANT" not in response_upper
    
    if is_relevant:
        print(f"  [OK] Chunk is RELEVANT")
    else:
        print(f"  [SKIP] Chunk is NOT_RELEVANT")
    
    return is_relevant

def generate_qa(chunks: List[Dict], expert_persona: str, domain: str) -> tuple:
    """Generate one or more Q&A pairs from multihop context chunks using consolidated prompt.
    
    Returns:
        Tuple of (qa_pairs, qa_metadata) where qa_metadata contains:
        - keywords_per_chunk: Dict mapping chunk identifiers to keyword lists
        - related_keywords: String describing keyword relationships (bridge keywords)
        - chunk_count: Number of chunks used in generation
    """
    print(f"Generating Q&A pairs from {len(chunks)} context chunks...")
    
    # Format prompt with or without domain
    if domain:
        domain_context = f" in the field of {domain}"
        domain_relevance = f" ({domain})"
    else:
        domain_context = ""
        domain_relevance = ""
    
    prompt = PROMPTS["question_answer_generation"].format(
        content="[Refer to the chunks provided below]",
        expert_persona=expert_persona,
        domain_context=domain_context,
        domain_relevance=domain_relevance
    )
    
    response = call_ai_service(
        prompt,
        chunks,
        stage="generation",
        response_format={"type": "json_object"},
    )
    
    # Parse multiple Q&A pairs from response using delimiter format
    qa_pairs = []
    qa_metadata = {
        'keywords_per_chunk': {},
        'related_keywords': '',
        'chunk_count': 0
    }
    tuple_delimiter = PROMPTS.get("DEFAULT_TUPLE_DELIMITER", "<|#|>")
    completion_delimiter = PROMPTS.get("DEFAULT_COMPLETION_DELIMITER", "<|#|>END<|#|>")
    
    try:
        structured_pairs, structured_metadata = _parse_json_qa_response(response)
        if structured_pairs:
            qa_metadata.update(structured_metadata)
            print(f"[OK] Generated {len(structured_pairs)} structured Q&A pair(s)")
            return structured_pairs, qa_metadata

        # Remove completion delimiter if present
        full_response = response
        if completion_delimiter in response:
            response = response.split(completion_delimiter)[0].strip()
    
        # Remove START delimiter if present at the beginning
        start_delimiter = tuple_delimiter + "START" + tuple_delimiter
        if start_delimiter in response:
            response = response.split(start_delimiter, 1)[-1].strip()
        
        # New format uses <|#|>QA_GENERATION<|#|> and <|#|>NEXT<|#|> sections
        qa_generation_marker = tuple_delimiter + "QA_GENERATION" + tuple_delimiter
        next_delimiter = tuple_delimiter + "NEXT" + tuple_delimiter
        decomposition_marker = tuple_delimiter + "DECOMPOSITION" + tuple_delimiter
        
        # Parse keyword metadata from the header section (before QA_GENERATION marker)
        if qa_generation_marker in response:
            header_section = response.split(qa_generation_marker)[0].strip()
            
            # Parse Chunk Count
            chunk_count_match = re.search(r'Chunk Count:\s*(\d+)', header_section, re.IGNORECASE)
            if chunk_count_match:
                qa_metadata['chunk_count'] = int(chunk_count_match.group(1))
            
            # Parse Keywords per Chunk: <Chunk 1: [A, B], Chunk 2: [C, D]>
            keywords_match = re.search(r'Keywords per Chunk:\s*<?(.+?)>?\s*(?=Related Keywords:|$)', header_section, re.IGNORECASE | re.DOTALL)
            if keywords_match:
                keywords_str = keywords_match.group(1).strip()
                # Parse format: Chunk 1: [A, B], Chunk 2: [C, D]
                chunk_pattern = re.findall(r'Chunk\s*(\d+):\s*\[([^\]]+)\]', keywords_str, re.IGNORECASE)
                for chunk_num, keywords in chunk_pattern:
                    keyword_list = [k.strip() for k in keywords.split(',')]
                    qa_metadata['keywords_per_chunk'][f'chunk_{chunk_num}'] = keyword_list
            
            # Parse Related Keywords (bridge keywords): <[A] relates to [C] via...>
            related_match = re.search(r'Related Keywords:\s*<?(.+?)>?\s*(?=<\|#\||$)', header_section, re.IGNORECASE | re.DOTALL)
            if related_match:
                qa_metadata['related_keywords'] = related_match.group(1).strip()
        
        # Split by QA_GENERATION or NEXT markers to get QA sections
        if qa_generation_marker in response:
            # New format: split by QA_GENERATION and NEXT
            sections = re.split(re.escape(qa_generation_marker) + r'|' + re.escape(next_delimiter), response)
            
            for section in sections:
                section = section.strip()
                if not section:
                    continue
                
                # Skip header section (contains Chunk Count, Keywords)
                if 'Chunk Count:' in section or 'Keywords per Chunk:' in section:
                    continue
                
                # Remove DECOMPOSITION section if present
                if decomposition_marker in section:
                    section = section.split(decomposition_marker)[0].strip()
                
                # Parse Question: and Answer: lines
                question_match = re.search(r'Question:\s*(.+?)(?=\n(?:Answer:|Relevance:|Difficulty:)|$)', section, re.DOTALL | re.IGNORECASE)
                answer_match = re.search(r'Answer:\s*(.+?)(?=\n(?:Relevance:|Difficulty:)|$)', section, re.DOTALL | re.IGNORECASE)
                relevance_match = re.search(r'Relevance:\s*(\d+)', section, re.IGNORECASE)
                difficulty_match = re.search(r'Difficulty:\s*(\d+)', section, re.IGNORECASE)
                
                if question_match and answer_match:
                    question = question_match.group(1).strip()
                    answer = answer_match.group(1).strip()
                    relevance = relevance_match.group(1) if relevance_match else "0"
                    difficulty = difficulty_match.group(1) if difficulty_match else "0"
                    
                    if question and answer:
                        qa_pairs.append({
                            "question": question,
                            "answer": answer,
                            "relevance_score": relevance,
                            "difficulty_score": difficulty
                        })
        
        # Fallback: try inline delimiter format (Question<|#|>...<|#|>Answer<|#|>...)
        if not qa_pairs:
            lines = [line.strip() for line in response.split('\n') if line.strip()]
            
            for line in lines:
                # Skip NEXT delimiter lines
                if line == next_delimiter:
                    continue
                
                # Check if line starts with "Question" delimiter pattern
                if line.startswith("Question" + tuple_delimiter) or line.startswith("question" + tuple_delimiter):
                    parts = line.split(tuple_delimiter)
                    
                    # Format: Question<|#|><text><|#|>Answer<|#|><text><|#|>Relevance<|#|><score><|#|>Difficulty<|#|><score>
                    if len(parts) >= 4 and parts[0].lower() == "question" and parts[2].lower() == "answer":
                        question = parts[1].strip()
                        answer = parts[3].strip()
                        relevance = "0"
                        difficulty = "0"
                        
                        if len(parts) >= 8:
                            if parts[4].lower() == "relevance":
                                relevance = parts[5].strip()
                            if parts[6].lower() == "difficulty":
                                difficulty = parts[7].strip()
                        
                        if question and answer:
                            qa_pairs.append({
                                "question": question,
                                "answer": answer,
                                "relevance_score": relevance,
                                "difficulty_score": difficulty
                            })
        
        # Final fallback: try old Question:/Answer: format
        if not qa_pairs:
            question_matches = re.finditer(r'(?i)Question:\s*(.*?)(?=\nAnswer:|\n\n|$)', response, re.DOTALL)
            answer_matches = re.finditer(r'(?i)Answer:\s*(.*?)(?=\nQuestion:|\n\n|$)', response, re.DOTALL)
    
            questions = [m.group(1).strip() for m in question_matches]
            answers = [m.group(1).strip() for m in answer_matches]
            
            if questions and answers and len(questions) == len(answers):
                for q, a in zip(questions, answers):
                    qa_pairs.append({
                        "question": q, 
                        "answer": a,
                        "relevance_score": "0",
                        "difficulty_score": "0"
                    })
            elif questions and answers:
                for i, q in enumerate(questions):
                    if i < len(answers):
                        qa_pairs.append({
                            "question": q, 
                            "answer": answers[i],
                            "relevance_score": "0",
                            "difficulty_score": "0"
                        })
            
            if not qa_pairs:
                print("[WARN] Could not parse Q&A from response")
                qa_pairs.append({
                    "question": response,
                    "answer": "",
                    "relevance_score": "0",
                    "difficulty_score": "0"
                })
        
        print(f"[OK] Generated {len(qa_pairs)} Q&A pair(s)")
        if qa_metadata['keywords_per_chunk']:
            print(f"   Keywords extracted: {len(qa_metadata['keywords_per_chunk'])} chunks")
        if qa_metadata['related_keywords']:
            print(f"   Bridge keywords: {qa_metadata['related_keywords'][:80]}...")
        return qa_pairs, qa_metadata
        
    except Exception as e:
        print(f"[WARN] Error parsing Q&A: {e}")
        import traceback
        print(traceback.format_exc())
        return [{
            "question": response, 
            "answer": "",
            "relevance_score": "0",
            "difficulty_score": "0"
        }], qa_metadata

def select_qa_pairs(
    qa_pairs: list,
    chunks: List[Dict],
    expert_persona: str,
    domain: str,
    use_model_review: bool = True,
) -> tuple[list, list]:
    """Filter malformed pairs locally and optionally run the selection agent."""
    print(f"Selecting Q&A pairs ({len(qa_pairs)} candidates)...")
    
    if not qa_pairs:
        return [], []
    
    eligible_pairs = []
    rejected_pairs = []
    for qa_pair in qa_pairs:
        qa_pair["short_answers"] = ensure_short_answers(qa_pair)
        violations = atomic_qa_violations(
            qa_pair.get("question", ""),
            qa_pair.get("answer", ""),
            qa_pair["short_answers"],
        )
        if violations:
            qa_pair["selection_status"] = "LOCAL_REJECTED"
            qa_pair["selection_reason"] = (
                "Deterministic atomic QA gate failed: " + ", ".join(violations)
            )
            rejected_pairs.append(qa_pair)
        else:
            eligible_pairs.append(qa_pair)

    if not eligible_pairs:
        print(f"[OK] Selection complete: 0 selected, {len(rejected_pairs)} rejected")
        return [], rejected_pairs

    if not use_model_review:
        for qa_pair in eligible_pairs:
            qa_pair["selection_status"] = "LOCAL_SELECTED"
            qa_pair["selection_reason"] = (
                "Passed deterministic atomic QA gate; optional model selection disabled."
            )
        print(
            f"[OK] Local selection complete: {len(eligible_pairs)} selected, "
            f"{len(rejected_pairs)} rejected (0 selection API calls)"
        )
        return eligible_pairs, rejected_pairs

    tuple_delimiter = PROMPTS.get("DEFAULT_TUPLE_DELIMITER", "<|#|>")
    completion_delimiter = PROMPTS.get("DEFAULT_COMPLETION_DELIMITER", "<|#|>END<|#|>")
    
    # Format domain context
    if domain:
        domain_context = f" in the field of {domain}"
        domain_relevance = f" ({domain})"
    else:
        domain_context = ""
        domain_relevance = ""
    
    # Prepare batch requests
    requests = []
    for qa_pair in eligible_pairs:
        prompt = PROMPTS["question_answer_selection"].format(
            content="[Refer to the chunks provided below]",
            question=qa_pair["question"],
            answer=qa_pair["answer"],
            expert_persona=expert_persona,
            domain_context=domain_context,
            domain_relevance=domain_relevance
        )
        requests.append((prompt, chunks))
    
    # Execute batch or sequential based on count
    if len(requests) > 1:
        print(f"  Batch evaluating {len(requests)} QA pairs...")
        responses = batch_call_vlm_interweaved(
            requests,
            show_progress=False,
            stage="selection",
        )
    else:
        responses = [call_ai_service(requests[0][0], chunks, stage="selection")]
    
    # Process responses
    selected_pairs = []
    
    for idx, (qa_pair, response) in enumerate(zip(eligible_pairs, responses), 1):
        try:
            if response and not response.startswith("ERROR:"):
                # Remove END delimiter if present
                if completion_delimiter in response:
                    response = response.split(completion_delimiter)[0].strip()
                
                # Remove START delimiter if present
                start_delimiter = tuple_delimiter + "START" + tuple_delimiter
                if start_delimiter in response:
                    response = response.split(start_delimiter, 1)[-1].strip()
                
                parts = response.split(tuple_delimiter)
                status = "REJECTED"
                relevance = "0"
                difficulty = "0"
                reason = "No reason provided"
                
                # Parse key-value pairs from delimiter format
                for i in range(len(parts)):
                    key = parts[i].strip().lower()
                    if i + 1 < len(parts):
                        value = parts[i + 1].strip()
                        
                        if key == "status":
                            status = value.upper()
                        elif key == "relevance":
                            relevance = value
                        elif key == "difficulty":
                            difficulty = value
                        elif key == "reason":
                            reason = value
                
                qa_pair["relevance_score"] = relevance
                qa_pair["difficulty_score"] = difficulty
                qa_pair["selection_reason"] = reason
                qa_pair["selection_status"] = status
                
                if status == "SELECTED":
                    selected_pairs.append(qa_pair)
                    print(f"    [OK] Q{idx} SELECTED (R:{relevance}/D:{difficulty})")
                else:
                    rejected_pairs.append(qa_pair)
                    print(f"    [FAIL] Q{idx} REJECTED: {reason[:60]}...")
            else:
                qa_pair["selection_status"] = "ERROR"
                qa_pair["selection_reason"] = f"API Error: {response}"
                rejected_pairs.append(qa_pair)
                
        except Exception as e:
            print(f"    [WARN] Error parsing selection response for Q{idx}: {e}")
            qa_pair["selection_status"] = "ERROR"
            qa_pair["selection_reason"] = f"Parsing error: {str(e)}"
            rejected_pairs.append(qa_pair)
    
    print(f"[OK] Selection complete: {len(selected_pairs)} selected, {len(rejected_pairs)} rejected")
    return selected_pairs, rejected_pairs

def verify_qa(chunks: List[Dict], question: str, answer: str, expert_persona: str, domain: str) -> str:
    """Verify if the question requires the content to be answered"""
    print("Verifying Q&A pair...")
    
    # Format prompt with or without domain
    if domain:
        domain_context = f" in the field of {domain}"
    else:
        domain_context = ""
    
    # Note: New prompt uses {questions} and {answers} (plural)
    prompt = PROMPTS["question_answer_verification"].format(
        content="[Refer to the chunks provided below]",
        questions=question,
        answers=answer,
        expert_persona=expert_persona,
        domain_context=domain_context
    )
    response = call_ai_service(prompt, chunks, stage="verification")
    return response


def batch_verify_qa(chunks: List[Dict], qa_pairs: List[Dict], expert_persona: str, domain: str) -> List[str]:
    """Batch verify multiple Q&A pairs using concurrent API calls
    
    Args:
        chunks: Context chunks for verification
        qa_pairs: List of dicts with 'question' and 'answer' keys
        expert_persona: Expert role string
        domain: Domain string
        
    Returns:
        List of verification result strings in same order as qa_pairs
    """
    if not qa_pairs:
        return []
    
    # Format domain context
    if domain:
        domain_context = f" in the field of {domain}"
    else:
        domain_context = ""
    
    # Prepare batch requests
    requests = []
    for qa in qa_pairs:
        # Note: New prompt uses {questions} and {answers} (plural)
        prompt = PROMPTS["question_answer_verification"].format(
            content="[Refer to the chunks provided below]",
            questions=qa['question'],
            answers=qa['answer'],
            expert_persona=expert_persona,
            domain_context=domain_context
        )
        requests.append((prompt, chunks))
    
    # Execute batch
    if len(requests) > 1:
        print(f"  Batch verifying {len(requests)} QA pairs...")
        responses = batch_call_vlm_interweaved(
            requests,
            show_progress=False,
            stage="verification",
        )
    else:
        responses = [call_ai_service(requests[0][0], chunks, stage="verification")]
    
    return responses


def _parse_single_chunk_shortcut_response(response: str) -> Tuple[str, str]:
    """Parse the anti-shortcut verifier response."""
    tuple_delimiter = PROMPTS.get("DEFAULT_TUPLE_DELIMITER", "<|#|>")
    status = "UNKNOWN"
    explanation = ""

    if response and tuple_delimiter in response:
        parts = response.split(tuple_delimiter)
        for i, part in enumerate(parts):
            key = part.strip().lower()
            if key == "status" and i + 1 < len(parts):
                candidate = parts[i + 1].strip().upper()
                if candidate in {"CAN_ANSWER", "PARTIAL_ONLY", "CANNOT_ANSWER"}:
                    status = candidate
            elif key == "explanation" and i + 1 < len(parts):
                explanation = parts[i + 1].strip()

    if status == "UNKNOWN" and response:
        upper = response.upper()
        if "CANNOT_ANSWER" in upper:
            status = "CANNOT_ANSWER"
        elif "PARTIAL_ONLY" in upper:
            status = "PARTIAL_ONLY"
        elif "CAN_ANSWER" in upper:
            status = "CAN_ANSWER"

    return status, explanation


def _chunk_source_id(chunk: Dict, idx: int) -> str:
    file_name = chunk.get("file_name", "unknown")
    chunk_id = chunk.get("global_chunk_id") or chunk.get("chunk_id", str(idx))
    return f"{file_name}:{chunk_id}"


def verify_multihop_necessity(
    chunks: List[Dict],
    question: str,
    answer: str,
    expert_persona: str,
    domain: str,
    min_supporting_chunks: int = 2,
    counterfactual_verification: bool = True,
    qa_pair: Dict | None = None,
    verification_mode: str = "balanced",
    max_verification_chunks: int = 4,
    max_unknown_chunks: int = 1,
) -> Dict:
    """Reject single-chunk shortcuts with balanced or exhaustive verification."""
    mode = str(verification_mode or "balanced").strip().lower()
    if mode not in {"balanced", "strict"}:
        logging.warning("Unknown multihop verification mode %r; using balanced", mode)
        mode = "balanced"

    usable_chunks = []
    chunk_labels = []
    seen_sources = set()
    for raw_index, chunk in enumerate(chunks, 1):
        if not isinstance(chunk, dict) or not str(chunk.get("content", "")).strip():
            continue
        label = _chunk_source_id(chunk, raw_index)
        if label in seen_sources:
            continue
        seen_sources.add(label)
        usable_chunks.append(chunk)
        chunk_labels.append(label)

    if len(chunk_labels) < min_supporting_chunks:
        return {
            "status": "INSUFFICIENT_CHUNKS",
            "passes": False,
            "min_supporting_chunks": min_supporting_chunks,
            "distinct_chunk_count": len(chunk_labels),
            "single_chunk_checks": [],
            "verification_mode": mode,
            "verification_api_calls": 0,
        }

    if domain:
        domain_context = f" in the field of {domain}"
    else:
        domain_context = ""

    if mode == "balanced":
        selected_indices = prioritize_verification_chunks(
            chunk_labels,
            qa_pair,
            max_chunks=max_verification_chunks,
            min_supporting_chunks=min_supporting_chunks,
        )
        selected_chunks = [usable_chunks[index] for index in selected_indices]
        selected_labels = [chunk_labels[index] for index in selected_indices]
        prompt = PROMPTS["consolidated_multihop_check"].format(
            question=question,
            answer=answer,
            expert_persona=expert_persona,
            domain_context=domain_context,
            chunk_count=len(selected_chunks),
        )
        response = call_ai_service(
            prompt,
            selected_chunks,
            stage="verification",
            response_format={"type": "json_object"},
        )
        statuses, checks = parse_consolidated_multihop_response(
            response,
            selected_labels,
        )
        gate = evaluate_multihop_gate(
            statuses,
            {},
            min_supporting_chunks=min_supporting_chunks,
            counterfactual_verification=False,
            max_unknown_chunks=max_unknown_chunks,
        )
        return {
            "status": gate["status"],
            "passes": gate["passes"],
            "min_supporting_chunks": min_supporting_chunks,
            "distinct_chunk_count": len(chunk_labels),
            "checked_chunk_count": len(selected_labels),
            "checked_chunks": selected_labels,
            "shortcut_chunks": gate["shortcut_chunks"],
            "unknown_single_chunks": gate["unknown_single_chunks"],
            "supporting_chunks": gate["partial_chunks"],
            "single_chunk_checks": checks,
            "counterfactual_verification": False,
            "counterfactual_checks": [],
            "necessary_chunks": [],
            "redundant_chunks": [],
            "minimal_evidence_count": 0,
            "verification_mode": mode,
            "verification_api_calls": 1,
            "method": "consolidated_single_pass",
        }

    requests = []
    for idx, chunk in enumerate(usable_chunks, 1):
        prompt = PROMPTS["single_chunk_shortcut_check"].format(
            question=question,
            answer=answer,
            expert_persona=expert_persona,
            domain_context=domain_context
        )
        requests.append((prompt, [chunk]))

    if len(requests) > 1:
        responses = batch_call_vlm_interweaved(
            requests,
            show_progress=False,
            stage="verification",
        )
    else:
        responses = [
            call_ai_service(requests[0][0], requests[0][1], stage="verification")
        ]

    checks = []
    shortcut_chunks = []
    unknown_chunks = []
    partial_chunks = []
    for label, response in zip(chunk_labels, responses):
        status, explanation = _parse_single_chunk_shortcut_response(response)
        check = {
            "chunk": label,
            "status": status,
            "explanation": explanation,
        }
        checks.append(check)
        if status == "CAN_ANSWER":
            shortcut_chunks.append(label)
        elif status == "UNKNOWN":
            unknown_chunks.append(label)
        elif status == "PARTIAL_ONLY":
            partial_chunks.append(label)

    counterfactual_checks = []
    ablation_statuses = {}
    if counterfactual_verification and not shortcut_chunks and not unknown_chunks:
        ablation_requests = []
        removed_labels = []
        for removed_idx, removed_label in enumerate(chunk_labels):
            remaining_chunks = [
                chunk for idx, chunk in enumerate(usable_chunks) if idx != removed_idx
            ]
            prompt = PROMPTS["counterfactual_ablation_check"].format(
                question=question,
                answer=answer,
                expert_persona=expert_persona,
                domain_context=domain_context,
            )
            ablation_requests.append((prompt, remaining_chunks))
            removed_labels.append(removed_label)

        if len(ablation_requests) > 1:
            ablation_responses = batch_call_vlm_interweaved(
                ablation_requests,
                show_progress=False,
                stage="verification",
            )
        else:
            ablation_responses = [
                call_ai_service(
                    ablation_requests[0][0],
                    ablation_requests[0][1],
                    stage="verification",
                )
            ]

        for removed_label, response in zip(removed_labels, ablation_responses):
            status_value, explanation = _parse_single_chunk_shortcut_response(response)
            is_necessary = status_value in {"PARTIAL_ONLY", "CANNOT_ANSWER"}
            counterfactual_checks.append({
                "removed_chunk": removed_label,
                "remaining_context_status": status_value,
                "necessary": is_necessary,
                "explanation": explanation,
            })
            ablation_statuses[removed_label] = status_value

    gate = evaluate_multihop_gate(
        {check["chunk"]: check["status"] for check in checks},
        ablation_statuses,
        min_supporting_chunks=min_supporting_chunks,
        counterfactual_verification=counterfactual_verification,
        max_unknown_chunks=0,
    )

    return {
        "status": gate["status"],
        "passes": gate["passes"],
        "min_supporting_chunks": min_supporting_chunks,
        "distinct_chunk_count": len(chunk_labels),
        "shortcut_chunks": gate["shortcut_chunks"],
        "single_chunk_checks": checks,
        "counterfactual_verification": counterfactual_verification,
        "counterfactual_checks": counterfactual_checks,
        "necessary_chunks": gate["necessary_chunks"],
        "redundant_chunks": gate["redundant_chunks"],
        "minimal_evidence_count": gate["minimal_evidence_count"],
        "verification_mode": mode,
        "verification_api_calls": len(requests) + len(counterfactual_checks),
        "method": "single_chunk_shortcut_plus_leave_one_out_ablation",
    }


def is_multihop_necessity_successful(result: Dict) -> bool:
    return bool(result and result.get("passes") is True)


def process_chunk_for_qa(chunk_data: Dict, expert_persona: str, domain: str) -> Dict:
    """Complete pipeline: build context, generate Q&A using pre-extracted role, verify"""
    chunk_id = chunk_data.get('chunk_id', 'unknown')
    chunk_content = chunk_data.get('content', '')
    
    print(f"\n{'='*80}")
    print(f"Processing chunk {chunk_id}")
    print(f"{'='*80}")
    
    # Stage 1: Build complete context using multi-hop retrieval
    print("\nStage 1: Building complete context...")
    context_result = build_complete_context(
        initial_chunk=chunk_data,
        max_depth=3,
        max_breadth=3,
        chunks_per_search=2,
        expert_persona=expert_persona,
        domain=domain,
        chunk_addition_mode=CHUNK_ADDITION_MODE
    )
    
    final_context = context_result['context']
    context_chunks = context_result.get('chunks', [])
    from oceangraph.core.config import is_text_only_mode
    if is_text_only_mode():
        from oceangraph.text import sanitize_text_chunks

        context_chunks = sanitize_text_chunks(context_chunks)
    completion_status = context_result['status']
    
    print(f"Context status: {completion_status}")
    print(f"Final context length: {len(final_context)} chars")
    print(f"Multihop context: {len(context_chunks)} chunks (original + retrieved)")
    
    # Stage 2: Use pre-extracted expert role and domain (from BERTopic analysis)
    print(f"\n[OK] Using expert role: {expert_persona}")
    print(f"[OK] Using domain: {domain}")
    
    # Stage 3: Generate Q&A pairs from multihop context
    print(f"\nStage 3: Generating Q&A pairs from multihop context ({len(context_chunks)} chunks)...")
    qa_pairs, qa_metadata = generate_qa(context_chunks, expert_persona, domain)
    
    # Stage 3.5: Select Q&A pairs
    print("\nStage 3.5: Selecting Q&A pairs...")
    selected_pairs, rejected_pairs = select_qa_pairs(qa_pairs, context_chunks, expert_persona, domain)
    
    # Stage 4: Verify selected Q&A pairs - BATCH PROCESSING
    verified_qa_pairs = []
    print(f"\nStage 4: Verifying {len(selected_pairs)} selected Q&A pair(s)...")
    
    if selected_pairs:
        # Use batch verification
        verification_results = batch_verify_qa(
            context_chunks, selected_pairs, expert_persona, domain
        )
        
        for i, (qa_pair, verification_result) in enumerate(zip(selected_pairs, verification_results), 1):
            question = qa_pair["question"]
            answer = qa_pair["answer"]
            qa_pair["short_answers"] = ensure_short_answers(qa_pair)
            evidence_graph = build_evidence_graph(context_chunks, qa_pair, qa_metadata)
            print(f"\n  Q&A {i}: {question[:80]}...")
            print(f"  Verification: {verification_result[:100] if verification_result else 'ERROR'}...")
            
            verified_qa_pairs.append({
                "question": question,
                "answer": answer,
                **get_structured_qa_fields(qa_pair),
                "relevance_score": qa_pair.get("relevance_score", "0"),
                "difficulty_score": qa_pair.get("difficulty_score", "0"),
                "selection_status": qa_pair.get("selection_status", "SELECTED"),
                "selection_reason": qa_pair.get("selection_reason", ""),
                "verification_result": verification_result or "ERROR",
                "evidence_graph": evidence_graph,
                "search_trajectory": build_search_trajectory(context_result),
            })
    
    return {
        "chunk_id": chunk_id,
        "original_chunk": chunk_content,
        "final_context": final_context,
        "context_chunks": context_chunks,
        "context_status": completion_status,
        "depth_reached": context_result['depth'],
        "chunks_added": context_result['chunks_added'],
        "search_history": context_result.get('search_history', []),
        "search_trajectory": build_search_trajectory(context_result),
        "expert_persona": expert_persona,
        "domain": domain,
        "keywords_per_chunk": qa_metadata.get('keywords_per_chunk', {}),
        "related_keywords": qa_metadata.get('related_keywords', ''),
        "selected_qa_pairs": verified_qa_pairs,
        "rejected_qa_pairs": rejected_pairs
    }

def has_misleading_visual_reference(question: str, answer: str, chunks: List[Dict] = None) -> bool:
    """Detect if question mentions visual content but answer doesn't need it.
    
    Returns True if the question has a misleading visual reference.
    """
    import re
    
    # Visual reference patterns in question
    visual_patterns = [
        r'\b(as\s+)?(depicted|shown|illustrated|displayed)\s+(in|by)\s+(the\s+)?(figure|diagram|schematic|image|chart|graph|picture)',
        r'\b(the\s+)?(figure|diagram|schematic|image|chart|graph|picture)\s+(shows|depicts|illustrates)',
        r'\bbased\s+on\s+(the\s+)?(figure|diagram|schematic|image|chart|graph|picture)',
        r'\baccording\s+to\s+(the\s+)?(figure|diagram|schematic|image|chart|graph|picture)',
        r'\b(in|from)\s+(the\s+)?(figure|diagram|schematic|image|chart|graph|picture)',
    ]
    
    question_lower = question.lower()
    has_visual_ref = any(re.search(p, question_lower) for p in visual_patterns)
    
    if not has_visual_ref:
        return False  # No visual reference, not misleading
    
    # Check if chunks actually have images
    has_images = False
    if chunks:
        for chunk in chunks:
            if chunk.get('image_path') or chunk.get('artifact'):
                has_images = True
                break
    
    # Check if answer references visual elements (suggesting it actually uses the image)
    visual_answer_patterns = [
        r'\b(the\s+)?(figure|diagram|image|chart|graph)\s+(shows|indicates|displays)',
        r'\bvisual(ly)?',
        r'\b(top|bottom|left|right|center)\s+(of|portion|section)',
        r'\b(axis|legend|label|arrow|line|curve|bar)',
    ]
    answer_lower = answer.lower()
    answer_uses_visual = any(re.search(p, answer_lower) for p in visual_answer_patterns)
    
    # Misleading if: question has visual ref BUT (no images in chunks OR answer doesn't use visual)
    if not has_images:
        return True  # Question mentions visual but no images exist
    if not answer_uses_visual:
        return True  # Question mentions visual but answer doesn't interpret any visual elements
    
    return False


def is_verification_successful(
    verification_result: str,
    question: str = None,
    answer: str = None,
    short_answers: List[str] = None,
    chunks: List[Dict] = None,
) -> bool:
    """Check if verification indicates success.
    
    New format: <|#|>START<|#|>Status<|#|><Label 1>, <Label 2>, <Label 3><|#|>Explanation<|#|><text><|#|>END<|#|>
    """
    required_good = ["QUESTION_CORRECT", "ANSWER_CORRECT", "REQUIRES_CONTENT"]
    bad_values = ["QUESTION_INCORRECT", "ANSWER_INCORRECT", "CAN_ANSWER_WITHOUT_CONTENT"]
    
    # Parse the status field from the new format
    tuple_delimiter = PROMPTS.get("DEFAULT_TUPLE_DELIMITER", "<|#|>")
    status_content = verification_result
    
    if tuple_delimiter in verification_result:
        parts = verification_result.split(tuple_delimiter)
        for i, part in enumerate(parts):
            if part.strip().lower() == "status" and i + 1 < len(parts):
                status_content = parts[i + 1].strip()
                break
    
    has_bad = any(bad in status_content.upper() for bad in bad_values)
    has_all_good = all(good in status_content.upper() for good in required_good)
    
    if answer and has_visible_self_correction(answer):
        return False

    if question and answer and atomic_qa_violations(question, answer, short_answers):
        return False

    # Additional code-level check for misleading visual references
    if question and answer and has_all_good and not has_bad:
        if has_misleading_visual_reference(question, answer, chunks):
            return False  # Fail due to misleading visual reference
    
    return has_all_good and not has_bad


def correct_failed_qa(chunks: List[Dict], failed_qa_pairs: List[Dict], 
                      expert_persona: str, domain: str) -> List[Dict]:
    """Generate corrected QA pairs from failed QA pairs using verification feedback.
    
    Args:
        chunks: Context chunks for QA generation
        failed_qa_pairs: List of dicts with 'question', 'answer', 'verification_result'
        expert_persona: Expert role string
        domain: Domain string
        
    Returns:
        List of corrected QA pair dicts with 'question', 'answer', 'relevance_score', 'difficulty_score'
    """
    if not failed_qa_pairs:
        return []
    
    print(f"Correcting {len(failed_qa_pairs)} failed Q&A pair(s)...")
    
    # Format the failed QA feedback section
    failed_qa_feedback_parts = []
    for i, qa in enumerate(failed_qa_pairs, 1):
        question = qa.get('question', '')
        answer = qa.get('answer', '')
        verification = qa.get('verification_result', 'No verification feedback available')
        
        failed_qa_feedback_parts.append(
            f"--- Failed QA #{i} ---\n"
            f"Question: {question}\n"
            f"Answer: {answer}\n"
            f"Verification Feedback: {verification}\n"
        )
    
    failed_qa_feedback = "\n".join(failed_qa_feedback_parts)
    
    # Format domain context
    if domain:
        domain_context = f" in the field of {domain}"
    else:
        domain_context = ""
    
    prompt = PROMPTS["question_answer_generation_corrected"].format(
        content="[Refer to the chunks provided below]",
        expert_persona=expert_persona,
        domain_context=domain_context,
        failed_qa_feedback=failed_qa_feedback
    )
    
    response = call_ai_service(prompt, chunks, stage="correction")
    
    # Parse corrected QA pairs (same format as generate_qa)
    corrected_pairs = []
    tuple_delimiter = PROMPTS.get("DEFAULT_TUPLE_DELIMITER", "<|#|>")
    completion_delimiter = PROMPTS.get("DEFAULT_COMPLETION_DELIMITER", "<|#|>END<|#|>")
    
    try:
        # Remove completion delimiter if present
        if completion_delimiter in response:
            response = response.split(completion_delimiter)[0].strip()
        
        # Remove START delimiter if present
        start_delimiter = tuple_delimiter + "START" + tuple_delimiter
        if start_delimiter in response:
            response = response.split(start_delimiter, 1)[-1].strip()
        
        # Check for empty response (no valid correction possible)
        if not response.strip() or response.strip() == tuple_delimiter + "START" + tuple_delimiter:
            print("  [WARN] No correction possible - content doesn't support the original topic")
            return []
        
        # Split by NEXT delimiter for multiple QA pairs
        next_delimiter = tuple_delimiter + "NEXT" + tuple_delimiter
        qa_sections = response.split(next_delimiter)
        
        for section_index, section in enumerate(qa_sections):
            section = section.strip()
            if not section:
                continue
            
            # Parse Question, Answer, Relevance, Difficulty from delimiter format
            parts = section.split(tuple_delimiter)
            qa_dict = {}
            
            for j in range(len(parts)):
                key = parts[j].strip()
                if j + 1 < len(parts):
                    value = parts[j + 1].strip()
                    
                    if key.lower() == "question":
                        qa_dict["question"] = value
                    elif key.lower() == "answer":
                        qa_dict["answer"] = value
                    elif key.lower() == "shortanswer":
                        qa_dict["short_answers"] = [value]
                    elif key.lower() == "answertype":
                        qa_dict["answer_type"] = value
                    elif key.lower() == "relevance":
                        qa_dict["relevance_score"] = value
                    elif key.lower() == "difficulty":
                        qa_dict["difficulty_score"] = value
            
            if qa_dict.get("question") and qa_dict.get("answer"):
                source = failed_qa_pairs[min(section_index, len(failed_qa_pairs) - 1)]
                for field_name in (
                    "question_type",
                    "answer_type",
                    "subdomain",
                    "sub_questions",
                    "reasoning_path",
                    "supporting_facts",
                    "evidence_spans",
                ):
                    if source.get(field_name) not in (None, "", []):
                        qa_dict.setdefault(field_name, source[field_name])
                declared_hops = source.get("declared_hop_count")
                if declared_hops is not None:
                    qa_dict.setdefault("hop_count", declared_hops)
                qa_dict["correction_status"] = "CORRECTED"
                corrected_pairs.append(qa_dict)
                print(f"  [OK] Corrected: {qa_dict['question'][:60]}...")
    
    except Exception as e:
        logging.error(f"Error parsing corrected QA response: {e}")
        print(f"  [ERROR] Error parsing correction response: {e}")
    
    print(f"  Generated {len(corrected_pairs)} corrected Q&A pair(s)")
    return corrected_pairs


if __name__ == "__main__":
    setup_logging()
    
    # Load chunks
    print(f"Loading chunks from {INPUT_CHUNKS_FILE}...")
    with open(INPUT_CHUNKS_FILE, 'r') as f:
        chunks = json.load(f)
    
    # Limit to first N chunks if MAX_CHUNKS is set
    if MAX_CHUNKS is not None:
        chunks = chunks[:MAX_CHUNKS]
        print(f"Processing {len(chunks)} chunks (limited to {MAX_CHUNKS} for testing)...")
    else:
        print(f"Processing all {len(chunks)} chunks...")
    
    # Extract domain and expert role once for all chunks using BERTopic
    print(f"\n{'='*80}")
    
    # Priority 1: Check config.yaml
    domain, expert_persona = None, None
    try:
        from oceangraph.core.config import get_domain_expert_config
        domain_config = get_domain_expert_config()
        config_domain = domain_config.get('domain')
        config_persona = domain_config.get('expert_persona')
        
        if config_domain and config_persona:
            print(f"[OK] Using domain and expert persona from config.yaml")
            domain, expert_persona = config_domain, config_persona
            save_domain_expert_to_env(domain, expert_persona)
    except ImportError:
        pass
    
    # Priority 2: Check environment variables
    if not domain or not expert_persona:
        env_domain, env_persona = load_domain_expert_from_env()
        if env_domain and env_persona:
            domain, expert_persona = env_domain, env_persona
    
    # Priority 3: Auto-detect using BERTopic
    if not domain or not expert_persona:
        print("Auto-detecting domain and expert persona from corpus...")
        domain, expert_persona = fetch_domain_and_role(INPUT_CHUNKS_FILE)
        # Note: fetch_domain_and_role already saves to environment variables
    
    print(f"[OK] Domain: {domain}")
    print(f"[OK] Expert Role: {expert_persona}")
    print(f"{'='*80}\n")
    
    # Initialize result containers
    successful_qa_pairs = []
    failed_qa_pairs = []
    irrelevant_chunks = []
    
    # Process each chunk: relevance check -> build multihop context -> generate QA -> select -> verify
    for i, chunk in tqdm(enumerate(chunks, 1), total=len(chunks), desc="Processing chunks"):
        tqdm.write(f"\n{'='*80}")
        tqdm.write(f"Processing Chunk {i}/{len(chunks)}")
        tqdm.write(f"Pipeline: Multihop Context -> QA Generation -> Selection -> Verification")
        tqdm.write(f"{'='*80}")
        
        try:
            # Extract chunk content and metadata
            if isinstance(chunk, dict):
                chunk_content = chunk.get("content", str(chunk))
                source_document = chunk.get("file_name", "unknown")
                chunk_id = chunk.get("chunk_id", str(i))
            else:
                chunk_content = str(chunk)
                source_document = "unknown"
                chunk_id = str(i)
            
            # Stage 0: Check chunk relevance
            print(f"\nStage 0: Checking chunk relevance...")
            is_relevant = check_chunk_relevance(chunk_content, expert_persona, domain)
            
            if not is_relevant:
                # Store irrelevant chunk and skip processing
                irrelevant_chunks.append({
                    "chunk_id": chunk_id,
                    "source_document": source_document
                })
                tqdm.write(f"[SKIP] Chunk {i} is NOT_RELEVANT - skipping processing")
                continue
            
            # Prepare chunk data
            if isinstance(chunk, dict):
                chunk_data = chunk
            else:
                chunk_data = {
                    "content": str(chunk),
                    "chunk_id": str(i),
                    "file_name": "unknown",
                    "artifact": "None"
                }

            # Process chunk with pre-extracted domain and role
            result = process_chunk_for_qa(chunk_data, expert_persona, domain)
            
            # Process selected Q&A pairs
            successful_count = 0
            context_chunks = result.get("context_chunks", [])
            for qa_pair in result.get("selected_qa_pairs", []):
                if is_verification_successful(
                    qa_pair.get("verification_result", ""),
                    question=qa_pair.get("question", ""),
                    answer=qa_pair.get("answer", ""),
                    short_answers=qa_pair.get("short_answers", []),
                    chunks=context_chunks
                ):
                    successful_count += 1
                    # Create individual entry for each successful Q&A pair
                    successful_qa_pairs.append({
                        "chunk_id": result["chunk_id"],
                        "original_chunk": result["original_chunk"],
                        "final_context": result["final_context"],
                        "context_chunks": result.get("context_chunks", []),  # Full chunks with image_path
                        "context_status": result["context_status"],
                        "depth_reached": result["depth_reached"],
                        "chunks_added": result["chunks_added"],
                        "search_history": result.get("search_history", []),
                        "keywords_per_chunk": result.get("keywords_per_chunk", {}),
                        "related_keywords": result.get("related_keywords", ""),
                        "expert_persona": result["expert_persona"],
                        "domain": result.get("domain", ""),
                        "question": qa_pair["question"],
                        "answer": qa_pair["answer"],
                        **get_structured_qa_fields(qa_pair),
                        "relevance_score": qa_pair.get("relevance_score", "0"),
                        "difficulty_score": qa_pair.get("difficulty_score", "0"),
                        "selection_status": qa_pair.get("selection_status", "SELECTED"),
                        "selection_reason": qa_pair.get("selection_reason", ""),
                        "verification_result": qa_pair["verification_result"]
                    })
                else:
                    # Create individual entry for each failed verification
                    failed_qa_pairs.append({
                        "chunk_id": result["chunk_id"],
                        "original_chunk": result["original_chunk"],
                        "final_context": result["final_context"],
                        "context_chunks": result.get("context_chunks", []),  # Full chunks with image_path
                        "context_status": result["context_status"],
                        "depth_reached": result["depth_reached"],
                        "chunks_added": result["chunks_added"],
                        "search_history": result.get("search_history", []),
                        "keywords_per_chunk": result.get("keywords_per_chunk", {}),
                        "related_keywords": result.get("related_keywords", ""),
                        "expert_persona": result["expert_persona"],
                        "domain": result.get("domain", ""),
                        "question": qa_pair["question"],
                        "answer": qa_pair["answer"],
                        **get_structured_qa_fields(qa_pair),
                        "relevance_score": qa_pair.get("relevance_score", "0"),
                        "difficulty_score": qa_pair.get("difficulty_score", "0"),
                        "selection_status": qa_pair.get("selection_status", "SELECTED"),
                        "selection_reason": qa_pair.get("selection_reason", ""),
                        "verification_result": qa_pair["verification_result"],
                        "failure_reason": "Failed verification"
                    })
            
            # Add rejected Q&A pairs to failed list
            for qa_pair in result.get("rejected_qa_pairs", []):
                failed_qa_pairs.append({
                    "chunk_id": result["chunk_id"],
                    "original_chunk": result["original_chunk"],
                    "final_context": result["final_context"],
                    "context_chunks": result.get("context_chunks", []),  # Full chunks with image_path
                    "context_status": result["context_status"],
                    "depth_reached": result["depth_reached"],
                    "chunks_added": result["chunks_added"],
                    "search_history": result.get("search_history", []),
                    "keywords_per_chunk": result.get("keywords_per_chunk", {}),
                    "related_keywords": result.get("related_keywords", ""),
                    "expert_persona": result["expert_persona"],
                    "domain": result.get("domain", ""),
                    "question": qa_pair["question"],
                    "answer": qa_pair["answer"],
                    **get_structured_qa_fields(qa_pair),
                    "relevance_score": qa_pair.get("relevance_score", "0"),
                    "difficulty_score": qa_pair.get("difficulty_score", "0"),
                    "selection_status": qa_pair.get("selection_status", "REJECTED"),
                    "selection_reason": qa_pair.get("selection_reason", ""),
                    "verification_result": "N/A - rejected by selection agent",
                    "failure_reason": "Rejected by selection agent"
                })
            
            total_qa = len(result.get("selected_qa_pairs", [])) + len(result.get("rejected_qa_pairs", []))
            if successful_count > 0:
                tqdm.write(f"[OK] {successful_count}/{total_qa} Q&A pair(s) passed all stages")
            else:
                tqdm.write(f"[WARN] 0/{total_qa} Q&A pairs passed all stages")
                
        except Exception as e:
            error_msg = f"[ERROR] Error processing chunk {i}: {e}"
            tqdm.write(error_msg)
            logging.error(error_msg)
            
            import traceback
            logging.error(traceback.format_exc())
            
            failed_qa_pairs.append({
                "chunk_id": i,
                "chunk_content": chunk_content if 'chunk_content' in locals() else str(chunk),
                "error": str(e),
                "traceback": traceback.format_exc()
            })
            continue
    
    # Save results
    print(f"\n{'='*80}")
    print("Saving results...")
    print(f"{'='*80}")
    
    if successful_qa_pairs:
        with open(OUTPUT_SUCCESSFUL, 'w', encoding='utf-8') as f:
            json.dump(successful_qa_pairs, f, indent=2, ensure_ascii=False)
        print(f"[OK] Successful QA pairs: {len(successful_qa_pairs)} saved to {OUTPUT_SUCCESSFUL}")
    
    if failed_qa_pairs:
        with open(OUTPUT_FAILED, 'w', encoding='utf-8') as f:
            json.dump(failed_qa_pairs, f, indent=2, ensure_ascii=False)
        print(f"[WARN] Failed QA pairs: {len(failed_qa_pairs)} saved to {OUTPUT_FAILED}")
    
    if irrelevant_chunks:
        with open(OUTPUT_IRRELEVANT, 'w', encoding='utf-8') as f:
            json.dump(irrelevant_chunks, f, indent=2, ensure_ascii=False)
        print(f"[SKIP] Irrelevant chunks: {len(irrelevant_chunks)} saved to {OUTPUT_IRRELEVANT}")
    
    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total chunks processed: {len(chunks)}")
    print(f"Relevant chunks processed: {len(chunks) - len(irrelevant_chunks)}")
    print(f"Irrelevant chunks skipped: {len(irrelevant_chunks)}")
    print(f"Successful QA pairs: {len(successful_qa_pairs)}")
    print(f"Failed QA pairs: {len(failed_qa_pairs)}")
    if len(chunks) - len(irrelevant_chunks) > 0:
        print(f"Success rate: {len(successful_qa_pairs)/(len(chunks) - len(irrelevant_chunks))*100:.1f}%")
    
    # Stats: Count single vs multiple chunks in successful QA pairs
    single_chunk_count = 0
    multiple_chunk_count = 0
    for qa_pair in successful_qa_pairs:
        chunks_added = qa_pair.get("chunks_added", [])
        if isinstance(chunks_added, list):
            if len(chunks_added) == 1:
                single_chunk_count += 1
            elif len(chunks_added) > 1:
                multiple_chunk_count += 1
    
    print(f"\nQA STATS")
    print(f"{'='*80}")
    print(f"Number of QA pairs in qa_multihop_fail: {len(failed_qa_pairs)}")
    print(f"Number of QA pairs with single chunk in qa_multihop_pass: {single_chunk_count}")
    print(f"Number of QA pairs with multiple chunks in qa_multihop_pass: {multiple_chunk_count}")
