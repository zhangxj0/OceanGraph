# OceanGraph v2.2.1 handoff

## Current state

- Source root: this directory (`OceanGraph/`).
- Framework/package version: `2.2.1`.
- Runtime architecture: Corpus, Evidence, QA, and Verifier Agents coordinated
  per candidate with ordered events and explicit feedback messages.
- Validated local regression command: `pytest -q`.
- Search-R1/RL training itself is outside this repository. OceanGraph produces
  verified training inputs; it does not run the downstream trainer.

## v2.2.1 correctness contract

- Deduplication selects an existing verified record and never rewrites a QA
  after verification.
- `hop_count` is the number of distinct verifier-grounded evidence chunks.
  `retrieval_hop_count` records retrieval expansion separately.
- Evidence graphs do not promote all context chunks when support is unresolved.
- QA correction is executed one source candidate at a time.
- Output and checkpoint reuse is guarded by a corpus/config fingerprint.
- The five-domain taxonomy is loaded from
  `src/oceangraph/ocean_taxonomy.yaml` at runtime.
- `configs/llm.yaml` is the only recommended user-editable model-routing file:
  Qwen owns generation stages and DeepSeek owns verification.
- `qa_generation.verification_profile: cost_efficient` performs local atomic,
  standalone, and short-answer checks before one consolidated DeepSeek call.
- Ground truth is one canonical answer (default maximum: 12 words or 16 CJK
  characters), identical to `short_answers[0]` after punctuation trimming.
- Model selection, counterfactual audits, and automatic correction are disabled
  in the recommended configuration to bound API cost.

## Training artifacts

A successful strict multi-hop run writes:

- `training/train.jsonl`: compact verified multi-agent QA rows;
- `training/corpus.jsonl`: evidence-ID-aligned retrieval corpus;
- `training/manifest.json`: export and rejection counts.

The exporter rejects records with incomplete Agent traces, failed verification,
fewer than two grounded evidence chunks, or inconsistent hop labels. It is also
available through `OceanGraphResults.export_training()`.

## Migration and local artifacts

- v2.2.0 output directories do not contain the v2.2.1 fingerprint manifest.
  Use a new output directory rather than mixing old and new artifacts.
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
