# OceanGraph-R1 Reproducibility Guide

This guide reproduces the validated DeepSeek text-only baseline and the
Search-R1 export path without storing credentials in the repository.

OceanGraph does not send images to model APIs. PDF figures may be extracted by
legacy ingestion code, but `pipeline.modality: text` removes their paths and
keeps only textual chunk content before generation and export.

## 1. Validated environment

- Ubuntu 24.04-compatible Linux
- Python 3.12
- NVIDIA RTX 4090 with 24 GB VRAM
- `deepseek-v4-pro` through the DeepSeek OpenAI-compatible API
- `BAAI/bge-m3` embeddings and FAISS retrieval

Unit tests also run on CPU-only machines. A CUDA GPU with at least 16 GB VRAM is
recommended for full corpus processing.

## 2. Install

```bash
git clone https://github.com/zhangxj0/OceanGraph.git
cd OceanGraph
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Run the deterministic local checks:

```bash
python -m compileall -q src scripts tests run_oceangraph.py
python -m pytest -q
python run_oceangraph.py --help
```

The validated revision reports 10 passing tests.

## 3. Configure DeepSeek securely

Never write the API key into YAML, shell scripts, logs, or Git history.

```bash
export DEEPSEEK_API_KEY="YOUR_ROTATED_KEY"
cp configs/deepseek.yaml.example config.deepseek.yaml
```

PowerShell equivalent:

```powershell
$env:DEEPSEEK_API_KEY = "YOUR_ROTATED_KEY"
Copy-Item configs/deepseek.yaml.example config.deepseek.yaml
```

The example routes generation, selection, verification, and correction through
`deepseek-v4-pro`. This baseline is text-only. Use the Qwen vision-capable
generator profile in `src/mirage/config.yaml.example` for image-bearing chunks.

## 4. Prepare a corpus

Place at least three related ocean-science TXT or Markdown documents in one
input directory. Each accepted question should require facts from at least two
different chunks.

```bash
mkdir -p data/repro_ocean
cp /path/to/ocean/files/*.md data/repro_ocean/
```

For the first smoke run, use a small corpus and request one accepted QA pair.

## 5. Cache embeddings

On a machine with internet access, cache BGE-M3 once:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"
```

On an isolated server, confirm the cache exists and add `--offline-models`.
This sets `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, preventing slow
Hugging Face network probes while retaining local GPU inference.

## 6. Run the validated baseline

```bash
python run_oceangraph.py \
  --config config.deepseek.yaml \
  --input data/repro_ocean \
  --output output/repro_deepseek \
  --backend openai \
  --model deepseek-v4-pro \
  --embedding-model bge_m3 \
  --reranker-model text_embedding \
  --offline-models \
  --num-qa-pairs 1 \
  --max-workers 1 \
  --max-depth 3 \
  --min-supporting-chunks 2
```

Remove `--offline-models` on the initial connected run if the embedding model is
not cached yet. Increase `--num-qa-pairs` only after the one-item smoke run
passes.

## 7. Validate outputs

The run is considered successful when:

1. `qa_multihop_pass.json` contains at least one record.
2. `verification_result` includes question, answer, and content-necessity checks.
3. `multihop_necessity_result.passes` is `true`.
4. At least two chunks are listed in `necessary_chunks`.
5. `evidence_graph` and `search_trajectory` are present.
6. No API key appears in logs or generated artifacts.

Important outputs are written under `output/repro_deepseek/`:

- `qa_multihop_pass.json` and `qa_multihop_pass.jsonl`
- `qa_multihop_fail.json` and `qa_multihop_fail.jsonl`
- `chunks.json`
- `chunks_with_complete_context.json`
- `oceangraph_run_config.json`

## 8. Export Search-R1 data

```bash
python scripts/oceangraph_to_search_r1.py \
  --qa-file output/repro_deepseek/qa_multihop_pass.json \
  --chunks-file output/repro_deepseek/chunks.json \
  --output-dir output/repro_deepseek/search_r1 \
  --short-answer-mode heuristic \
  --no-parquet
```

Verify that `conversion_summary.json` reports `converted > 0`. The export also
contains `train.jsonl`, `corpus.jsonl`, and `oceangraph_2wiki_like.jsonl`.

## 9. Reproducibility controls

- Keep `shuffling.seed: 42` fixed.
- Record the Git commit SHA, model ID, API endpoint, and corpus checksum.
- Keep temperature at `0.0` for every routed profile.
- Preserve accepted and rejected records for quality-gate auditing.
- Compare schema validity, acceptance rate, necessary chunk count, token usage,
  and Search-R1 conversion count across repeated runs.

API responses can still vary because the remote model service is not guaranteed
to be bitwise deterministic. Structural tests and evidence-necessity checks are
the stable reproducibility criteria.
