# OceanGraph v3.0.0 handoff

## Current state

- Source root: this directory (`OceanGraph/`).
- Framework/package version: `3.0.0`.
- Runtime architecture: Corpus, Evidence, QA, and Verifier Agents coordinated
  per candidate with ordered events and explicit feedback messages.
- Validated local regression command: `pytest -q`.
- Search-R1/RL training itself is outside this repository. OceanGraph produces
  verified training inputs; it does not run the downstream trainer.

## v3.0.0 correctness contract

- Deduplication selects an existing verified record and never rewrites a QA
  after verification.
- `hop_count` is the number of distinct verifier-grounded evidence chunks.
  `retrieval_hop_count` records retrieval expansion separately.
- Evidence graphs do not promote all context chunks when support is unresolved.
- QA correction is executed one source candidate at a time.
- Output and checkpoint reuse is guarded by a corpus/config fingerprint.
- The fingerprint includes semantic generation settings and model routes but
  excludes targets, worker counts, and output paths, allowing smoke runs to
  resume at formal scale.
- Mandatory local preflight failures skip all paid/model-loading probes; local
  model checks run in killable child processes.
- The five-domain taxonomy is loaded from
  `src/oceangraph/ocean_taxonomy.yaml` at runtime.
- `configs/llm.yaml` is the only recommended user-editable model-routing file:
  Qwen owns generation stages and DeepSeek owns verification. Both validated
  profiles use the Paratera endpoint and resolve `OPENAI_API_KEY` at runtime.
- Default semantic chunking uses an 8,000-character window with 800-character
  overlap and 4,096 output tokens to avoid truncated verbatim chunk responses.
- Corpus discovery is recursive and processes all source files by default;
  duplicate filename stems are rejected before checkpoint IDs can collide.
- Empty or reasoning-only HTTP 200 model responses are retried and never cached.
- `qa_generation.verification_profile: cost_efficient` performs local atomic,
  standalone, and short-answer checks before one consolidated DeepSeek call.
- Ground truth is one canonical answer (default maximum: 12 words or 16 CJK
  characters), identical to `short_answers[0]` after punctuation trimming.
- Model selection, counterfactual audits, and automatic correction are disabled
  in the recommended configuration to bound API cost.

## Training artifacts

A successful strict multi-hop run writes:

- `training/train.jsonl`, `training/dev.jsonl`, and `training/test.jsonl`:
  deterministic source-document-disjoint multi-agent QA rows;
- `training/corpus.jsonl`: evidence-ID-aligned retrieval corpus;
- `training/manifest.json`: split counts, source-leakage audit, export and
  rejection counts, plus formal split-readiness diagnostics.

The exporter rejects records with incomplete Agent traces, failed verification,
fewer than two grounded evidence chunks, or inconsistent hop labels. It is also
available through `OceanGraphResults.export_training()`.

Checkpoint and LLM-cache updates are append-only JSONL journals. Legacy JSON
snapshots remain readable, while new writes fail loudly if durability cannot be
guaranteed. QA scheduling keeps at most one worker-width, target-bounded batch
in flight so a nearly complete run does not launch a fixed ten-chunk batch.

## Migration and local artifacts

- Pre-v3.0 material output directories do not contain the v3.0 semantic
  fingerprint contract. Use a new output directory rather than mixing old and
  new material artifacts.
- Do not delete or move ignored contents under `data/`, `output/`, or `tmp/`
  without checking them manually; they may contain expensive local results.
- Never store API keys, tokens, server credentials, or a secret-bearing local
  `config.yaml` in the repository. Use environment variables.

## Remaining engineering work

- PDF/HTML ingestion options still need a dedicated Docling compatibility pass.
- The legacy standalone generation helpers in `pipeline/qa_generator.py` do not
  emit the full four-Agent training contract; use the main engine/API path.
- End-to-end generation with production model endpoints must be rerun after
  choosing the final corpus and credentials.
