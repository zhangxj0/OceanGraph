# OceanGraph-R1

<p align="center">
  <strong>A domain-aware multi-agent framework for building evidence-grounded ocean science multi-hop QA datasets.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-2.1.0-005F73.svg" alt="Version 2.1.0">
  <img src="https://img.shields.io/badge/python-3.12-blue.svg" alt="Python 3.12">
  <img src="https://img.shields.io/badge/license-Apache--2.0-green.svg" alt="Apache-2.0 license">
  <img src="https://img.shields.io/badge/domain-ocean%20science-0077B6.svg" alt="Ocean science">
</p>

**Current release:** `v2.1.0` · **Release branch:** `v2.1.0` ·
**Last updated:** `2026-07-17`

OceanGraph-R1 turns ocean-science corpora into structured, verifiable multi-hop
question-answer datasets for retrieval and reasoning evaluation. It accepts
PDF, HTML, TXT, and Markdown sources, plans domain-specific reasoning paths,
and verifies that each accepted question requires evidence from multiple chunks.

<p align="center">
  <img src="figures/oceangraph_main_figure.svg" alt="OceanGraph-R1 workflow" width="100%">
</p>

## Highlights

- **Ocean-domain planning** — Uses a five-domain ocean taxonomy covering
  physical oceanography and climate, carbon and biogeochemistry, remote sensing
  and observing systems, marine ecology and fisheries, and coastal hazards and
  human systems.
- **Atomic evidence-grounded multi-hop QA** — Asks for one minimal final
  answer while preserving hidden multi-step reasoning paths, supporting facts,
  and evidence spans; compound questions and single-chunk shortcuts are rejected.
- **Text-only corpus generation** — Converts PDF, HTML, TXT, and Markdown
  sources into text chunks and never sends extracted images to model APIs.
- **Structured outputs** — Exports accepted and rejected QA pairs as JSON and
  JSONL together with chunks and completed context.
- **Configurable model backends** — Supports Gemini, OpenAI, and local Ollama
  backends, with configurable embedding and reranking models.

## Installation

```bash
git clone https://github.com/zhangxj0/OceanGraph.git
cd OceanGraph
python -m venv .venv
```

Activate the virtual environment, then install the package:

```bash
pip install -e .
```

For migration to the validated Paratera NVIDIA image, reuse its preinstalled
Torch build and install the exact versions from `requirements.txt`:

```bash
python -m pip install --user --break-system-packages --no-deps \
  -r requirements.txt
python -m pip install --user --break-system-packages -e . --no-deps
```

`faiss-cpu` is required by multi-hop vector retrieval. Docling is no longer
required for TXT/Markdown inputs; PDF/HTML ingestion remains an optional
document-processing path.

Evaluation uses the configured DeepSeek verification route and the same local
BGE-M3 installation as retrieval; no Gemini, LangChain, or RAGAS packages are
required.

For the validated Qwen generation plus DeepSeek verification setup,
isolated-server deployment, validation criteria, and Search-R1 conversion
steps, see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Quick start

Set the API key for your selected backend:

```bash
# PowerShell
$env:OPENAI_API_KEY = "YOUR_OPENAI_KEY"

# bash / zsh
export OPENAI_API_KEY="YOUR_OPENAI_KEY"
```

For the recommended stage-routed setup, keep credentials in environment
variables and copy the `models` section from `configs/oceangraph.yaml.example`:

```powershell
Copy-Item configs/oceangraph.yaml.example config.yaml
$env:PARATERA_API_KEY = "YOUR_PARATERA_KEY"
$env:DEEPSEEK_API_KEY = "YOUR_DEEPSEEK_KEY"
```

This routes corpus analysis, retrieval, generation, and correction to
`Qwen3.7-Plus` through Paratera, while final text-only verification uses
`deepseek-v4-pro`. Optional model selection is routed to DeepSeek but disabled
by default because the deterministic atomic-QA gate already removes malformed
candidates. The default `pipeline.modality: text` setting strips image artifacts
before retrieval, generation, verification, and dataset export.

Run an OceanGraph pipeline over an input directory:

```bash
python run_oceangraph.py \
  --config config.yaml \
  --input data/ocean_texts \
  --output output/oceangraph_demo \
  --backend openai \
  --embedding-model bge_m3 \
  --offline-models \
  --reranker-model text_embedding \
  --num-qa-pairs 20 \
  --max-depth 2 \
  --min-supporting-chunks 2
```

Use `--offline-models` on isolated servers after the embedding model has been
cached locally. The equivalent YAML setting is
`embedding.local_files_only: true`; both forms prevent Hugging Face network
probes while retaining local GPU inference.

Or use the installed command:

```bash
oceangraph \
  --input data/ocean_texts \
  --output output/oceangraph_demo \
  --backend gemini \
  --api-key YOUR_GEMINI_KEY \
  --num-qa-pairs 20
```

Run environment checks before a full job:

```bash
python run_oceangraph.py --preflight
```

## Pipeline

OceanGraph-R1 coordinates three stages:

1. **Domain Corpus Agent** labels source material using the ocean taxonomy and
   assembles high-value multi-chunk contexts.
2. **Evidence Reasoning Agent** generates questions, answers, sub-questions,
   reasoning paths, and citation-ready evidence spans.
3. **QA Verification Agent** validates evidence coverage and strict multi-hop
   requirements before accepting an item.

The default `balanced` verifier keeps the single-chunk shortcut guard but checks
up to four evidence-prioritized chunks in one consolidated DeepSeek request. It
accepts a candidate when no checked chunk can answer alone and at least two
chunks provide partial evidence; one unparseable chunk verdict is tolerated.
Irrelevant background chunks do not cause rejection.

For an accepted candidate with `N` context chunks, the previous default used
`2 + 2N` verifier requests: model selection, full QA verification, `N`
single-chunk checks, and `N` leave-one-out checks. The recommended default uses
two requests: full QA verification plus one consolidated multi-hop check. With
four chunks this reduces verifier request count from 10 to 2. Use
`multihop_verification_mode: strict`, `model_selection: true`, and
`counterfactual_verification: true` only for exhaustive audit subsets.

## Output

A completed run writes the following key artifacts to the output directory:

| File | Description |
| --- | --- |
| `qa_multihop_pass.json` | Accepted multi-hop QA pairs |
| `qa_multihop_pass.jsonl` | JSONL version of accepted QA pairs |
| `qa_multihop_fail.json` | Rejected candidates and verification details |
| `qa_multihop_fail.jsonl` | JSONL version of rejected candidates |
| `chunks.json` | Source chunks used by the pipeline |
| `chunks_with_complete_context.json` | Context-expanded chunks |
| `oceangraph_run_config.json` | Run metadata and selected configuration |

Each accepted record includes fields such as `question_type`, `answer_type`,
`subdomain`, `declared_hop_count`, `sub_questions`, `reasoning_path`,
`supporting_facts`, and `evidence_spans`.

## Ocean taxonomy

The built-in taxonomy in `src/oceangraph/ocean_taxonomy.yaml` contains five
primary research domains:

1. Physical oceanography and climate
2. Carbon cycle and marine biogeochemistry
3. Remote sensing and observing systems
4. Marine ecology and fisheries
5. Coastal hazards and human systems

See `OCEAN_5_DOMAIN_DATASET.md` for the recommended corpus and dataset
organization, and `OCEANGRAPH_FRAMEWORK.md` for a detailed framework overview.

## Command-line options

```text
--input, -i                 Directory containing PDF, HTML, TXT, or Markdown inputs
--output, -o                Destination for generated dataset artifacts
--backend, -b               gemini, openai, or ollama
--embedding-model           bge_m3, bge_large, or auto
--offline-models            Use only locally cached Hugging Face models
--reranker-model            text_embedding
--num-qa-pairs              Target number of accepted QA pairs
--max-depth                 Maximum multi-hop retrieval depth
--min-supporting-chunks     Minimum distinct chunks for strict verification
--multihop-verification-mode {balanced,strict}
                            Choose consolidated or exhaustive shortcut checks
--max-verification-chunks   Cap evidence chunks checked in balanced mode
--max-unknown-verdicts      Allowed uncertain verdicts in balanced mode
--model-selection           Enable optional model-based candidate selection
--counterfactual-verification
                            Enable leave-one-out checks in strict mode
--no-counterfactual-verification
                            Disable leave-one-out evidence necessity checks
--no-strict-multihop        Disable the single-chunk shortcut check
--no-jsonl                  Disable JSONL output copies
--preflight                 Run environment checks only
```

## Project layout

```text
OceanGraph/
├── src/oceangraph/         # Unified public API and generation engine
├── scripts/                # Dataset and conversion helpers
├── figures/                # Framework illustrations
├── run_oceangraph.py       # Standalone entry point
├── OCEANGRAPH_FRAMEWORK.md # Detailed framework description
└── OCEAN_5_DOMAIN_DATASET.md
```

## License

This project is licensed under the [Apache License 2.0](LICENSE).
