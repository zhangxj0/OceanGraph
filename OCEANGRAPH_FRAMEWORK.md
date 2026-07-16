# OceanGraph-R1

OceanGraph-R1 is a domain-aware multi-agent framework for constructing
evidence-grounded and strictly verified multi-hop QA datasets in ocean science.

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
| Domain Corpus Agent | Converts heterogeneous ocean-science documents into semantic chunks and applies the five-domain ocean taxonomy. |
| Evidence Reasoning Agent | Completes multi-hop evidence context through iterative retrieval, evidence selection, and cross-chunk reasoning. |
| QA Verification Agent | Generates structured QA records, rejects single-chunk shortcuts, and builds supporting facts, evidence spans, and evidence-graph supervision. |

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

## Paper-Facing Contribution Summary

OceanGraph-R1 contributes a unified three-agent data construction structure for
ocean science search reasoning: domain-aware corpus modeling, recursive evidence
reasoning, adversarial single-chunk shortcut rejection, and evidence-graph
supervision.
