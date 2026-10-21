# Run outputs

Experiment outputs generated with the v4.0.0 pipeline (GLM-5.3 via an
OpenAI-compatible endpoint, `configs/llm.glm-deepseek.yaml.example` shows the
profile shape). All runs live under this directory; each keeps its own run
config, logs and exports.

| Directory | What it is |
| --- | --- |
| `glm53_low_smoke_20261019/` | Low-volume smoke run of the four-agent pipeline. |
| `glm53_practical50_20261019_1716/` | 50-sample practical-multihop run (first pass). |
| `glm53_practical50_20261019_1716_v2/` | 50-sample rerun with label normalization and surgical repairs (`repairs_applied.json`, `surgical_repairs.json`). |
| `glm53_practical20k_20261019_1914/` | 20k-target durable batch run. Stopped at 16171/20000 accepted when the model endpoint returned HTTP 403 — see `progress.json` and `dataset_summary.json` for the final accounting. `qa_partial.jsonl`, `training/` and `search_r1/` hold the accepted samples and exports as of the stop. |
| `test50/`, `test50_run.log` | 50-document configuration test run. |

Not committed from the 20k run: the `run.sqlite` resume database and
`worker.lock`/`worker.pid` (machine-local batch state) and `sources.jsonl`
(125 MB copy of the normalized corpus, reproducible from `data/normalized`).
