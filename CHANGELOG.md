# Changelog

All notable changes to OceanGraph-R1 are documented here.

## [3.0.0] - 2026-07-22

### Added
- Training-export readiness auditing with empty-split, connected-component,
  unresolved-evidence, and largest-component statistics.
- Killable subprocess isolation for local embedding and reranker preflight
  checks; API probes use one attempt with a bounded request timeout.

### Fixed
- Separated immutable dataset semantics from operational controls in the run
  fingerprint, so a two-record smoke run can resume in the same output
  directory with a larger target or worker count.
- Deferred output-manifest commitment until mandatory preflight succeeds and
  allowed stale manifests to be replaced when no material dataset exists.
- Made preflight fail-safe: Qwen, DeepSeek, and local model checks are skipped
  after a mandatory local prerequisite fails, and later expensive checks stop
  after the first expensive failure.
- Rejected training records whose supporting chunk IDs cannot be resolved in
  the exported retrieval corpus.

### Changed
- Advanced framework, Agent architecture, taxonomy, QA schema, configuration,
  runner, and package versions to `3.0.0`.
- Training manifests now expose `split_viable`; smoke runs may have empty
  held-out splits, but formal downstream training must require this flag to be
  `true`.

## [2.2.1] - 2026-07-22

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
- Deterministic source-document-component train/dev/test splitting with a
  leakage audit in the training manifest.
- Append-only checkpoint and LLM-cache journals with legacy JSON migration.

### Fixed
- Raised Qwen and DeepSeek output budgets to 4,096 tokens, corrected the
  `DeepSeek-V4-Pro` deployment name, and rejected empty reasoning-only responses
  instead of caching them as successful calls.
- Made source discovery recursive for nested normalized archives, rejected
  duplicate source stems, and aligned preflight discovery with the engine.
- Removed the hidden five-document fallback limit and reduced semantic
  chunking defaults to an 8,000-character window with 800-character overlap.
- Defined `hop_count` consistently as the number of distinct verified evidence
  chunks and separated retrieval expansion into `retrieval_hop_count`.
- Stopped evidence graphs from treating every context chunk as supporting
  evidence or inventing bridge edges without a declared support order.
- Changed QA correction to one-to-one candidate processing so missing or
  reordered model outputs cannot silently drop failed records.
- Made verified-record-preserving deduplication, runtime configuration isolation,
  and Verifier-to-Evidence/QA feedback routing the default execution behavior.
- Corrected CLI/API failure propagation, moved effective-config fingerprinting
  before paid preflight calls, and skipped evaluation-only model checks when
  evaluation is disabled.

### Changed
- Replaced the fixed `1.1 * target` seed-chunk ceiling with target-driven
  demand-bounded generation that keeps no more in-flight seed chunks than the
  remaining accepted-QA target and stops at the target or true corpus exhaustion.
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
