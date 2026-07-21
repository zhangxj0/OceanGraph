# Changelog

All notable changes to OceanGraph-R1 are documented here.

## [2.2.1] - 2026-07-21

- Isolated Qwen/DeepSeek endpoint and model routing in `configs/llm.yaml`; API
  keys remain environment-only.
- Added the default `cost_efficient` validation profile: deterministic local
  QA gates followed by at most one consolidated DeepSeek request per candidate.
- Enforced one standalone question and one canonical short EM ground truth
  (12 words or 16 CJK characters by default).
- Disabled optional model selection, counterfactual verification, and automatic
  correction in the recommended configuration to avoid repeat API charges.

### Added
- Strict downstream-training export with compact QA JSONL, an ID-aligned
  retrieval corpus, and a manifest containing record-level rejection counts.
- Corpus/config fingerprints and per-fingerprint checkpoint namespaces to
  prevent stale state or artifacts from being mixed across runs.
- A runtime-loaded canonical five-domain ocean taxonomy.

### Fixed
- Defined `hop_count` consistently as the number of distinct verified evidence
  chunks and separated retrieval expansion into `retrieval_hop_count`.
- Stopped evidence graphs from treating every context chunk as supporting
  evidence or inventing bridge edges without a declared support order.
- Changed QA correction to one-to-one candidate processing so missing or
  reordered model outputs cannot silently drop failed records.
- Made verified-record-preserving deduplication, runtime configuration isolation,
  and Verifier-to-Evidence/QA feedback routing the default execution behavior.

### Changed
- Replaced the fixed `1.1 * target` seed-chunk ceiling with target-driven
  batched generation that stops only at the accepted-QA target or true corpus
  exhaustion.
- Updated package, runtime Agent, configuration, runner, documentation, and CI
  metadata to `2.2.1`.
- Positioned generated records as inputs for downstream model training; no
  experimental ablation workflow is required by the v2.2.1 data pipeline.

## [2.2.0] - 2026-07-17

### Added
- Explicit Corpus, Evidence, QA, and Verifier runtime roles backed by the
  validated v2.1 pipeline functions.
- An ordered `agent_trace` on generated and rejected QA records, including
  role status and principal outputs.
- A public four-agent manifest and schema support for agent provenance.

### Changed
- Split QA synthesis/correction ownership from independent verification in the
  runtime orchestration layer.
- Updated CLI metadata, configuration templates, framework documentation, and
  the main methodology figure to the four-agent architecture.
- Aligned all package version declarations on `2.2.0`.

## [2.1.0] - 2026-07-16

### Added
- A deterministic atomic-QA quality gate that rejects compound questions,
  multiple answer targets, non-minimal answers, and mismatched short answers.
- Regression coverage for real compound multi-hop failures in Chinese.

### Changed
- Generation now produces one user-facing question with one canonical minimal
  answer while retaining hidden multi-hop sub-questions and evidence traces.
- Selection, verification, and correction prompts now enforce the same atomic
  multi-hop output contract.

## [2.0.0] - 2026-07-15

### Added
- Stage-routed text generation with Qwen and independent DeepSeek verification.
- Evidence graphs, search trajectories, counterfactual evidence checks, and
  Search-R1 conversion helpers.
- A public Python API through `OceanGraph`, `OceanGraphConfig`, and
  `OceanGraphResults`.

### Changed
- Consolidated the full implementation under the single `oceangraph` package.
- Standardized runtime settings on the `OCEANGRAPH_*` environment prefix.
- Made text-only dataset generation the default and excluded visual artifacts
  before retrieval, generation, verification, and export.
- Moved the recommended configuration to `configs/oceangraph.yaml.example`.

### Removed
- The legacy package namespace, command-line entry points, demos, and branded
  assets that duplicated OceanGraph functionality.

## [1.0.0] - 2026-01-06

### Added
- Initial multi-hop context retrieval, QA generation, verification,
  deduplication, and evaluation pipeline.
