# OceanGraph-R1

OceanGraph-R1 is a domain-aware multi-agent framework for constructing
evidence-grounded and cost-bounded multi-hop QA datasets in ocean science.

The framework turns heterogeneous ocean science documents into dataset records
that include one canonical minimal answer for EM/F1 reward, supporting facts,
evidence spans, evidence graphs, and retrieval traces for audit.

Each user-facing question is atomic: it requests one final answer span. Multiple
`sub_questions` remain hidden reasoning annotations used to identify bridge
entities and traverse evidence, rather than separate requests concatenated into
the visible question.

## Multi-Agent Architecture

| Agent | Role |
|---|---|
| Corpus Agent | Converts heterogeneous ocean-science documents into semantic chunks, applies the five-domain ocean taxonomy, and builds the retrieval index. |
| Evidence Agent | Detects information gaps and completes multi-hop evidence context through iterative retrieval and evidence selection. |
| QA Agent | Generates atomic questions, minimal answers, hidden sub-questions, reasoning paths, supporting facts, and evidence spans. |
| Verifier Agent | Independently checks atomicity, evidence grounding, and multi-hop necessity, then emits the final acceptance decision and evidence graph. |

The v3.0.0 runtime writes an ordered `agent_trace` and explicit coordination
state to every QA record. The trace
distinguishes generation from verification while the v3.0.0 data contract
enforces standalone questions, canonical short answers, and grounded evidence.

Generation and validation are model-separated through `configs/llm.yaml`.
Corpus, evidence-retrieval, and QA stages route to Qwen; the Verifier Agent
routes to DeepSeek. Under the default `cost_efficient` profile, deterministic
checks reject non-standalone, compound, or non-canonical short-answer records
before any verifier request. One DeepSeek request then jointly checks grounding
and multi-chunk support. Failed records are not automatically regenerated.

## Main Commands

Run a direct framework generation job:

```bash
python run_oceangraph.py \
  --input data/ocean_texts \
  --output output/oceangraph_demo \
  --backend openai \
  --api-key YOUR_API_KEY \
  --embedding-model bge_m3 \
  --reranker-model text_embedding \
  --num-qa-pairs 20 \
  --max-depth 2 \
  --min-supporting-chunks 2
```

Run one of the five domain pipelines:

```bash
python scripts/run_01_physical_ocean_climate.py
python scripts/run_02_carbon_biogeochemistry.py
python scripts/run_03_remote_sensing_observing.py
python scripts/run_04_marine_ecology_fisheries.py
python scripts/run_05_coastal_hazards_human.py
```

## Dataset Fields

Accepted QA samples include:

- `question`, `answer`, and `short_answers`
- `question_type`, `answer_type`, and `subdomain`
- `sub_questions` and `reasoning_path`
- `supporting_facts` and `evidence_spans`
- `evidence_graph`
- `search_history` and `search_trajectory`
- `multihop_necessity_result`
- `agent_trace`
- `coordination_trace`

`hop_count` is the number of distinct verifier-grounded evidence chunks. It is
not the number of retrieval iterations; that process label is exported as
`retrieval_hop_count`. Evidence graphs remain unresolved instead of promoting
all context chunks when explicit or verifier-grounded support is unavailable.

## Downstream Training Export

Each successful run produces source-document-disjoint `training/train.jsonl`,
`training/dev.jsonl`, and `training/test.jsonl`, together with
`training/corpus.jsonl` and `training/manifest.json`. Training rows contain compact SFT messages,
canonical and short answers, reasoning annotations, evidence supervision,
retrieval trajectories, and the four-Agent provenance. Full context text is
kept in the aligned corpus rather than duplicated in every QA row.

All source documents connected by a QA evidence graph are treated as one split
component. This prevents the same source document from appearing in training
and held-out QA, while a fixed seed keeps the assignment reproducible.

The v3.0 exporter resolves every supporting chunk against the aligned corpus
before accepting a training row. Its manifest reports empty splits, component
counts, the largest connected-component fraction, and `split_viable`. Formal
training requires a viable, leakage-free split; a two-sample smoke run remains
useful for pipeline validation but is not presented as evaluation-ready data.

The training `answer` is the single canonical EM ground truth, rather than a
rationale or explanatory paragraph. Multi-step reasoning remains in separate
reasoning and evidence fields. Its `answer_type` is restricted to `entity`,
`numeric`, `date`, `yes_no`, or length-bounded `short_text`; open-ended
descriptions and multi-value lists are not training targets.

## Paper-Facing Contribution Summary

OceanGraph-R1 contributes a unified four-agent data construction structure for
ocean science search reasoning: domain-aware corpus modeling, recursive evidence
completion, atomic QA synthesis, independent cost-bounded verification, and
training-ready evidence and Agent-trajectory supervision.
