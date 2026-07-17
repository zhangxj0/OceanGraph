# Changelog

All notable changes to OceanGraph-R1 are documented here.

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
