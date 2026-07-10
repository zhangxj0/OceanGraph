#!/usr/bin/env python3
"""Convert QA output into EM/F1-friendly Search-R1 training files."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_PROMPT_TEMPLATE = (
    "Answer the given question. You must put your final answer in "
    "<answer>...</answer>.\n\nQuestion: {question}"
)


def load_records(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    item = json.loads(line)
                    if isinstance(item, dict):
                        records.append(item)
        return records

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("qa_pairs"), list):
        return [item for item in data["qa_pairs"] if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def uniq(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        cleaned = normalize_space(item).strip(" .;,")
        key = cleaned.casefold()
        if cleaned and key not in seen:
            seen.add(key)
            output.append(cleaned)
    return output


def first_sentence(text: str) -> str:
    text = normalize_space(text)
    if not text:
        return ""
    match = re.search(r"(?<=[.!?])\s+", text)
    return text[: match.start()].strip() if match else text


def strip_intro_phrase(text: str) -> str:
    text = normalize_space(text)
    patterns = [
        r"^the\s+(?:two|three|four|five)\s+[^.]{0,80}?\s+are\s+",
        r"^the\s+[^.]{0,80}?\s+(?:is|are)\s+",
        r"^(?:it|they|these|those)\s+(?:is|are)\s+",
        r"^the\s+answer\s+(?:is|are)\s+",
        r"^answer:\s*",
    ]
    for pattern in patterns:
        stripped = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
        if stripped != text:
            return stripped
    return text


def reorder_pair_alias(answer: str) -> list[str]:
    if "," in answer:
        return []
    parts = re.split(r"\s+and\s+", answer, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2:
        return []
    left, right = [part.strip(" .;,") for part in parts]
    if not left or not right:
        return []
    return [f"{right} and {left}"]


def heuristic_short_answers(item: dict[str, Any], max_words: int) -> list[str]:
    existing = item.get("short_answers") or item.get("answer_aliases") or item.get("aliases")
    if isinstance(existing, str):
        existing = [existing]
    if isinstance(existing, list):
        cleaned_existing = [str(value) for value in existing if str(value).strip()]
        if cleaned_existing:
            return uniq(cleaned_existing)

    answer = normalize_space(str(item.get("answer", "")))
    answer_type = normalize_space(str(item.get("answer_type", ""))).lower()
    candidates: list[str] = []

    if answer_type in {"yes_no", "boolean"}:
        lowered = answer.lower()
        if lowered.startswith("yes"):
            candidates.append("yes")
        elif lowered.startswith("no"):
            candidates.append("no")

    if answer_type == "numeric":
        numeric = re.search(r"[-+]?\d[\d,]*(?:\.\d+)?(?:\s*%|\s*[A-Za-z/]+)?", answer)
        if numeric:
            candidates.append(numeric.group(0))

    sentence = strip_intro_phrase(first_sentence(answer))
    if sentence:
        candidates.append(sentence)

    if len(sentence.split()) > max_words:
        before_explanation = re.split(
            r"\s+(?:because|by|through|when|while|which|that|, reducing|, isolating)\s+",
            sentence,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        candidates.append(before_explanation)

    output = uniq(candidates)
    if output:
        output.extend(reorder_pair_alias(output[0]))
    return uniq(output)


def llm_short_answers(
    item: dict[str, Any],
    api_url: str,
    model: str,
    api_key_env: str,
    timeout: int,
) -> list[str]:
    api_key = os.getenv(api_key_env)
    if not api_key:
        raise RuntimeError(f"Environment variable {api_key_env} is not set")

    import requests

    prompt = f"""
Extract exact-match reward targets for this QA item.

Rules:
- Return JSON only: {{"short_answers": ["canonical answer", "alias"]}}
- Answers must be minimal spans suitable for EM/F1 reward.
- Prefer entity names, ordered/unordered list strings, numbers, or yes/no.
- Do not include explanations, evidence, or full sentences.
- Include common aliases or reordered two-item lists when useful.

Question: {item.get("question", "")}
Long answer: {item.get("answer", "")}
Answer type: {item.get("answer_type", "")}
Evidence: {json.dumps(item.get("evidence_spans", []), ensure_ascii=False)}
""".strip()

    response = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0,
            "max_tokens": 160,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end <= start:
        return []
    parsed = json.loads(content[start : end + 1])
    values = parsed.get("short_answers", [])
    if isinstance(values, str):
        values = [values]
    return uniq([str(value) for value in values if str(value).strip()])


def build_context(item: dict[str, Any]) -> list[list[Any]]:
    context = []
    seen: set[tuple[str, str]] = set()
    for chunk in item.get("context_chunks", []) or []:
        if not isinstance(chunk, dict):
            continue
        title = str(chunk.get("file_name") or chunk.get("chunk_id") or "chunk")
        content = normalize_space(str(chunk.get("content", "")))
        key = (title, content)
        if content and key not in seen:
            seen.add(key)
            context.append([title, [content]])
    return context


def supporting_chunk_ids(item: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for chunk in item.get("context_chunks", []) or []:
        if not isinstance(chunk, dict):
            continue
        file_name = str(chunk.get("file_name") or "chunk")
        chunk_id = str(chunk.get("chunk_id") or "")
        ids.append(f"{file_name}:{chunk_id}" if chunk_id else file_name)
    return uniq(ids)


def convert_corpus(chunks_file: Path | None) -> list[dict[str, str]]:
    if not chunks_file:
        return []
    chunks = load_records(chunks_file)
    corpus: list[dict[str, str]] = []
    seen: set[str] = set()
    for idx, chunk in enumerate(chunks):
        raw_id = chunk.get("global_chunk_id") or chunk.get("chunk_id") or idx
        doc_id = str(raw_id)
        if doc_id in seen:
            file_name = str(chunk.get("file_name") or "doc")
            doc_id = f"{file_name}:{doc_id}"
        seen.add(doc_id)
        content = normalize_space(str(chunk.get("content", "")))
        if content:
            corpus.append({"id": doc_id, "contents": content})
    return corpus


def to_search_r1_row(
    item: dict[str, Any],
    idx: int,
    short_answers: list[str],
    data_source: str,
    ability: str,
    split: str,
    prompt_template: str,
) -> dict[str, Any]:
    question = normalize_space(str(item.get("question", "")))
    return {
        "data_source": data_source,
        "prompt": [{"role": "user", "content": prompt_template.format(question=question)}],
        "ability": ability,
        "reward_model": {"style": "rule", "ground_truth": {"target": short_answers}},
        "extra_info": {
            "split": split,
            "index": idx,
            "question": question,
            "short_answers": short_answers,
            "long_answer": normalize_space(str(item.get("answer", ""))),
            "answer_type": item.get("answer_type", ""),
            "question_type": item.get("question_type", ""),
            "supporting_facts": item.get("supporting_facts", []),
            "evidence_spans": item.get("evidence_spans", []),
            "evidence_graph": item.get("evidence_graph", {}),
            "search_trajectory": item.get("search_trajectory", []),
            "search_history": item.get("search_history", []),
            "supporting_chunk_ids": supporting_chunk_ids(item),
            "source_chunk_id": item.get("chunk_id"),
        },
    }


def to_2wiki_like_row(
    item: dict[str, Any],
    idx: int,
    short_answers: list[str],
    id_prefix: str,
) -> dict[str, Any]:
    return {
        "_id": str(item.get("id") or item.get("qa_id") or f"{id_prefix}_{idx:06d}"),
        "question": normalize_space(str(item.get("question", ""))),
        "answer": short_answers[0] if short_answers else normalize_space(str(item.get("answer", ""))),
        "answer_aliases": short_answers,
        "long_answer": normalize_space(str(item.get("answer", ""))),
        "type": item.get("question_type", "bridge"),
        "answer_type": item.get("answer_type", ""),
        "supporting_facts": item.get("supporting_facts", []),
        "evidence_spans": item.get("evidence_spans", []),
        "context": build_context(item),
        "evidence_graph": item.get("evidence_graph", {}),
        "search_trajectory": item.get("search_trajectory", []),
        "search_history": item.get("search_history", []),
        "reasoning_path": item.get("reasoning_path", ""),
        "sub_questions": item.get("sub_questions", []),
    }


def write_parquet(path: Path, records: list[dict[str, Any]]) -> bool:
    try:
        import pandas as pd

        pd.DataFrame(records).to_parquet(path, index=False)
        return True
    except Exception as exc:  # pragma: no cover - depends on optional engines
        print(f"[WARN] Could not write parquet: {exc}", file=sys.stderr)
        return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qa-file", required=True, type=Path, help="QA pass JSON/JSONL file")
    parser.add_argument("--chunks-file", type=Path, help="chunks.json file for Search-R1 corpus")
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--split", default="train")
    parser.add_argument("--data-source", default="oceangraph_ocean")
    parser.add_argument("--ability", default="fact-reasoning")
    parser.add_argument("--wiki-output-name", default="oceangraph_2wiki_like.jsonl")
    parser.add_argument("--id-prefix", default="oceangraph")
    parser.add_argument("--prompt-template", default=DEFAULT_PROMPT_TEMPLATE)
    parser.add_argument("--short-answer-mode", choices=["heuristic", "llm"], default="heuristic")
    parser.add_argument("--max-short-answer-words", type=int, default=12)
    parser.add_argument("--api-url", default="https://api.deepseek.com/chat/completions")
    parser.add_argument("--model", default="deepseek-chat")
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--no-parquet", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    qa_items = load_records(args.qa_file)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    search_rows: list[dict[str, Any]] = []
    wiki_rows: list[dict[str, Any]] = []
    skipped = 0

    for idx, item in enumerate(qa_items):
        if args.short_answer_mode == "llm":
            try:
                short_answers = llm_short_answers(
                    item, args.api_url, args.model, args.api_key_env, args.timeout
                )
            except Exception as exc:
                print(f"[WARN] LLM short-answer extraction failed for row {idx}: {exc}", file=sys.stderr)
                short_answers = []
            if not short_answers:
                short_answers = heuristic_short_answers(item, args.max_short_answer_words)
        else:
            short_answers = heuristic_short_answers(item, args.max_short_answer_words)

        if not short_answers:
            skipped += 1
            continue

        enriched_item = {**item, "short_answers": short_answers}
        search_rows.append(
            to_search_r1_row(
                enriched_item,
                idx,
                short_answers,
                args.data_source,
                args.ability,
                args.split,
                args.prompt_template,
            )
        )
        wiki_rows.append(to_2wiki_like_row(enriched_item, idx, short_answers, args.id_prefix))

    write_jsonl(args.output_dir / f"{args.split}.jsonl", search_rows)
    write_jsonl(args.output_dir / args.wiki_output_name, wiki_rows)

    corpus = convert_corpus(args.chunks_file)
    if corpus:
        write_jsonl(args.output_dir / "corpus.jsonl", corpus)

    parquet_written = False
    if not args.no_parquet:
        parquet_written = write_parquet(args.output_dir / f"{args.split}.parquet", search_rows)

    summary = {
        "input_qa": len(qa_items),
        "converted": len(search_rows),
        "skipped_without_short_answer": skipped,
        "corpus_docs": len(corpus),
        "parquet_written": parquet_written,
        "data_source": args.data_source,
        "wiki_output_name": args.wiki_output_name,
        "id_prefix": args.id_prefix,
    }
    (args.output_dir / "conversion_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
