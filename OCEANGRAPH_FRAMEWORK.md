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

The v2.2 runtime writes an ordered `agent_trace` to every QA record. The trace
distinguishes generation from verification without changing the validated v2.1
retrieval, prompting, or acceptance semantics.

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

## Paper-Facing Contribution Summary

OceanGraph-R1 contributes a unified four-agent data construction structure for
ocean science search reasoning: domain-aware corpus modeling, recursive evidence
completion, atomic QA synthesis, independent cost-bounded verification, optional
exhaustive counterfactual auditing, and evidence-graph supervision.
