# OceanGraph-R1 Multi-Hop QA Workflow

OceanGraph-R1 provides a text-first and multimodal-ready workflow for building
ocean-domain multi-hop QA datasets with explicit evidence supervision.

## What changed

- TXT, MD, and Markdown files can be placed directly in the input directory.
- The framework also converts PDFs/HTML into the same chunking format.
- Generated QA pairs prefer a structured JSON schema with:
  - `question_type`
  - `answer_type`
  - `subdomain`
  - `declared_hop_count`
  - `sub_questions`
  - `reasoning_path`
  - `supporting_facts`
  - `evidence_spans`
- Strict multi-hop verification rejects QA pairs answerable from any single
  chunk.
- Successful and failed QA files are also exported as JSONL by default.
- `src/oceangraph/ocean_taxonomy.yaml` defines the ocean label set used by
  the Domain Planning Agent.

## Suggested quick run

```bash
python run_oceangraph.py \
  --input data/ocean_texts \
  --output output/oceangraph_ocean_qa \
  --backend openai \
  --api-key YOUR_OPENAI_KEY \
  --embedding-model bge_m3 \
  --reranker-model text_embedding \
  --num-qa-pairs 20 \
  --max-depth 2 \
  --min-supporting-chunks 2
```

For Gemini:

```bash
python run_oceangraph.py \
  --input data/ocean_texts \
  --output output/oceangraph_ocean_qa \
  --backend gemini \
  --api-key YOUR_GEMINI_KEY \
  --embedding-model bge_m3 \
  --num-qa-pairs 20
```

## Useful switches

- `--no-strict-multihop`: disables single-chunk shortcut checks.
- `--min-supporting-chunks N`: changes the strict verifier threshold.
- `--no-jsonl`: writes only JSON outputs.

## Main outputs

- `qa_multihop_pass.json`
- `qa_multihop_pass.jsonl`
- `qa_multihop_fail.json`
- `qa_multihop_fail.jsonl`
- `chunks.json`
- `chunks_with_complete_context.json`

## Notes

For server validation, start with a small target such as `--num-qa-pairs 5`.
Strict shortcut checking adds extra LLM calls, roughly one call per context chunk
for every selected QA candidate.
