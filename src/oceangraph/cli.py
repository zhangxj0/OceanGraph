#!/usr/bin/env python3
"""OceanGraph-R1 command line entry point.

This module provides a paper-facing wrapper around the internal generation
engine. It keeps the stable pipeline implementation intact while presenting the
system as an ocean-domain multi-agent dataset construction framework.
"""

from __future__ import annotations

import argparse
import json
import logging
import multiprocessing as mp
import os
import sys
from pathlib import Path
from typing import Optional

import yaml

from oceangraph import (
    AGENT_ARCHITECTURE_VERSION,
    FRAMEWORK_NAME,
    FRAMEWORK_VERSION,
    get_agent_manifest,
)


def configured_api_key_envs(config_path: Optional[str], backend: str) -> list[str]:
    """Return standard and stage-routed API key environment variables."""
    default_env = {
        "gemini": "GEMINI_API_KEY",
        "openai": "OPENAI_API_KEY",
    }.get(backend.lower())
    env_names = [default_env] if default_env else []
    path = Path(config_path) if config_path else None
    if path and path.is_file():
        try:
            config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            config = {}
        models = config.get("models") or {}
        profiles = models.get("profiles", {}) if isinstance(models, dict) else {}
        for profile in profiles.values():
            if not isinstance(profile, dict):
                continue
            profile_backend = str(profile.get("backend", backend)).lower()
            api_key_env = profile.get("api_key_env")
            if profile_backend == backend.lower() and api_key_env:
                env_names.append(str(api_key_env))
    return list(dict.fromkeys(env_names))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "OceanGraph-R1: a domain-aware multi-agent framework for generating "
            "evidence-grounded ocean science multi-hop QA datasets"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_oceangraph.py -i data/ocean_docs -o output/oceangraph_demo
  python run_oceangraph.py -i data/ocean_docs -o output/oceangraph_demo --backend openai --api-key YOUR_KEY
  python run_oceangraph.py -i data/ocean_docs -o output/oceangraph_demo --deduplication --evaluation

Pipeline agents:
  1. Corpus Agent
  2. Evidence Agent
  3. QA Agent
  4. Verifier Agent
""",
    )

    parser.add_argument("--input", "-i", type=str, help="Input directory containing PDF, HTML, TXT, or Markdown documents")
    parser.add_argument("--output", "-o", type=str, help="Output directory for generated dataset files")
    parser.add_argument("--backend", "-b", choices=["gemini", "openai", "ollama"], default="gemini")
    parser.add_argument("--api-key", "-k", type=str, help="API key for the selected backend")
    parser.add_argument("--model", type=str, help="Model name to use")
    parser.add_argument("--config", "-c", type=str, default="config.yaml", help="Path to configuration file")
    parser.add_argument("--preflight", action="store_true", help="Run environment checks only")
    parser.add_argument("--skip-pdf-processing", action="store_true", help="Use existing markdown outputs")
    parser.add_argument("--skip-chunking", action="store_true", help="Use existing chunks.json")
    parser.add_argument("--deduplication", action="store_true", help="Enable QA deduplication")
    parser.add_argument("--evaluation", action="store_true", help="Enable evaluation metrics")
    parser.add_argument("--num-qa-pairs", type=int, default=100, help="Target number of accepted QA pairs")
    parser.add_argument("--max-workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--embedding-model", default="bge_m3", help="Text embedding model: bge_m3, bge_large, or auto")
    parser.add_argument("--offline-models", action="store_true", help="Use only locally cached Hugging Face models")
    parser.add_argument("--reranker-model", default="text_embedding", help="Text reranker model")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum depth for multi-hop context retrieval")
    parser.add_argument("--no-strict-multihop", action="store_true", help="Disable single-chunk shortcut checks")
    counterfactual_group = parser.add_mutually_exclusive_group()
    counterfactual_group.add_argument(
        "--counterfactual-verification",
        dest="counterfactual_verification",
        action="store_true",
        help="Enable exhaustive leave-one-out evidence necessity checks in strict mode",
    )
    counterfactual_group.add_argument(
        "--no-counterfactual-verification",
        dest="counterfactual_verification",
        action="store_false",
        help="Disable leave-one-out evidence necessity checks",
    )
    counterfactual_group.set_defaults(counterfactual_verification=None)
    parser.add_argument(
        "--multihop-verification-mode",
        choices=["balanced", "strict"],
        help="Balanced uses one consolidated call; strict checks chunks exhaustively",
    )
    parser.add_argument(
        "--max-verification-chunks",
        type=int,
        help="Maximum evidence-prioritized chunks checked in balanced mode",
    )
    parser.add_argument(
        "--max-unknown-verdicts",
        type=int,
        help="Allowed uncertain chunk verdicts in balanced mode",
    )
    parser.add_argument(
        "--model-selection",
        action="store_true",
        help="Enable the optional model-based QA selection stage",
    )
    parser.add_argument("--min-supporting-chunks", type=int, help="Minimum distinct chunks required by strict verification")
    parser.add_argument("--no-jsonl", action="store_true", help="Do not write JSONL copies of QA outputs")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--version", action="version", version=f"%(prog)s {FRAMEWORK_VERSION}")
    return parser.parse_args()


def setup_environment(args: argparse.Namespace) -> None:
    """Expose command-line options through OceanGraph environment variables."""
    if args.config:
        os.environ["OCEANGRAPH_CONFIG"] = args.config

    if args.api_key:
        for env_name in configured_api_key_envs(args.config, args.backend):
            os.environ[env_name] = args.api_key

    backend = args.backend.upper()
    os.environ["OCEANGRAPH_BACKEND"] = backend

    if args.model:
        os.environ["OCEANGRAPH_MODEL"] = args.model

    counterfactual_verification = getattr(
        args, "counterfactual_verification", None
    )
    if counterfactual_verification is None and getattr(
        args, "no_counterfactual_verification", False
    ):
        counterfactual_verification = False
    if counterfactual_verification is not None:
        os.environ["OCEANGRAPH_COUNTERFACTUAL_VERIFICATION"] = (
            "1" if counterfactual_verification else "0"
        )
    if getattr(args, "multihop_verification_mode", None):
        os.environ["OCEANGRAPH_MULTIHOP_VERIFICATION_MODE"] = (
            args.multihop_verification_mode
        )
    if getattr(args, "max_verification_chunks", None):
        os.environ["OCEANGRAPH_MAX_VERIFICATION_CHUNKS"] = str(
            args.max_verification_chunks
        )
    if getattr(args, "max_unknown_verdicts", None) is not None:
        os.environ["OCEANGRAPH_MAX_UNKNOWN_VERDICTS"] = str(
            args.max_unknown_verdicts
        )
    if getattr(args, "model_selection", False):
        os.environ["OCEANGRAPH_MODEL_SELECTION"] = "1"

    if args.input:
        os.environ["OCEANGRAPH_INPUT_DIR"] = args.input
    if args.output:
        os.environ["OCEANGRAPH_OUTPUT_DIR"] = args.output

    if args.num_qa_pairs:
        os.environ["OCEANGRAPH_NUM_QA_PAIRS"] = str(args.num_qa_pairs)
    if args.max_workers:
        os.environ["OCEANGRAPH_MAX_WORKERS"] = str(args.max_workers)
    if args.embedding_model:
        os.environ["OCEANGRAPH_EMBEDDING_MODEL"] = args.embedding_model
    if args.offline_models:
        os.environ["OCEANGRAPH_OFFLINE_MODELS"] = "1"
    if args.reranker_model:
        os.environ["OCEANGRAPH_RERANKER_MODEL"] = args.reranker_model
    if args.max_depth:
        os.environ["OCEANGRAPH_MAX_DEPTH"] = str(args.max_depth)
    if args.no_strict_multihop:
        os.environ["OCEANGRAPH_STRICT_MULTIHOP"] = "0"
    if args.min_supporting_chunks:
        os.environ["OCEANGRAPH_MIN_SUPPORTING_CHUNKS"] = str(args.min_supporting_chunks)
    if args.no_jsonl:
        os.environ["OCEANGRAPH_OUTPUT_JSONL"] = "0"

    if args.deduplication:
        os.environ["OCEANGRAPH_RUN_DEDUPLICATION"] = "1"
    if args.evaluation:
        os.environ["OCEANGRAPH_RUN_EVALUATION"] = "1"


def validate_args(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if args.input and not Path(args.input).exists():
        errors.append(f"Input directory does not exist: {args.input}")

    if not args.preflight and args.backend != "ollama":
        env_names = configured_api_key_envs(args.config, args.backend)
        api_key = args.api_key or next(
            (os.environ.get(env_name) for env_name in env_names if os.environ.get(env_name)),
            None,
        )
        if not api_key:
            env_hint = " or ".join(env_names)
            errors.append(f"API key required for {args.backend}. Use --api-key or set {env_hint}.")
    return errors


def write_run_metadata(args: argparse.Namespace) -> None:
    if not args.output:
        return
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        from oceangraph.core.config import load_config

        qa_config = load_config().get("qa_generation", {})
    except Exception:
        qa_config = {}

    strict_multihop = qa_config.get("strict_multihop_verification", True)
    if os.environ.get("OCEANGRAPH_STRICT_MULTIHOP") is not None:
        strict_multihop = os.environ["OCEANGRAPH_STRICT_MULTIHOP"] == "1"
    model_selection = qa_config.get("model_selection", False)
    if os.environ.get("OCEANGRAPH_MODEL_SELECTION") is not None:
        model_selection = os.environ["OCEANGRAPH_MODEL_SELECTION"] == "1"
    counterfactual = qa_config.get("counterfactual_verification", False)
    if os.environ.get("OCEANGRAPH_COUNTERFACTUAL_VERIFICATION") is not None:
        counterfactual = (
            os.environ["OCEANGRAPH_COUNTERFACTUAL_VERIFICATION"] == "1"
        )
    verification_mode = str(os.environ.get(
        "OCEANGRAPH_MULTIHOP_VERIFICATION_MODE",
        qa_config.get("multihop_verification_mode", "balanced"),
    ) or "balanced").strip().lower()
    if verification_mode not in {"balanced", "strict"}:
        verification_mode = "balanced"
    if verification_mode != "strict":
        counterfactual = False

    metadata = {
        "framework": FRAMEWORK_NAME,
        "framework_version": FRAMEWORK_VERSION,
        "input_dir": args.input,
        "output_dir": args.output,
        "backend": args.backend,
        "model": args.model,
        "num_qa_pairs": args.num_qa_pairs,
        "max_workers": args.max_workers,
        "embedding_model": args.embedding_model,
        "reranker_model": args.reranker_model,
        "max_depth": args.max_depth,
        "qa_verification": {
            "strict_multihop_verification": strict_multihop,
            "model_selection": model_selection,
            "multihop_verification_mode": verification_mode,
            "max_verification_chunks": int(os.environ.get(
                "OCEANGRAPH_MAX_VERIFICATION_CHUNKS",
                qa_config.get("max_verification_chunks", 4),
            )),
            "max_unknown_verdicts": int(os.environ.get(
                "OCEANGRAPH_MAX_UNKNOWN_VERDICTS",
                qa_config.get("max_unknown_verdicts", 1),
            )),
            "counterfactual_verification": counterfactual,
        },
        "agents": [spec["agent_id"] for spec in get_agent_manifest()],
        "agent_architecture": {
            "version": AGENT_ARCHITECTURE_VERSION,
            "sequence": ["corpus", "evidence", "qa", "verifier"],
            "manifest": get_agent_manifest(),
        },
    }
    (output_dir / "oceangraph_run_config.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 76)
    logger.info("  %s: Ocean Science Multi-Agent Dataset Generator", FRAMEWORK_NAME)
    logger.info("=" * 76)

    setup_environment(args)

    try:
        from oceangraph.engine import run_pipeline
        from oceangraph.utils.preflight import run_preflight_checks
    except ImportError as exc:
        logger.error("Failed to import the internal generation engine: %s", exc)
        logger.info("Install the project with: pip install -e .")
        sys.exit(1)

    if args.preflight:
        logger.info("Running preflight checks...")
        success = run_preflight_checks()
        sys.exit(0 if success else 1)

    if not args.input or not args.output:
        logger.error("Both --input and --output are required.")
        logger.info("Usage: python run_oceangraph.py --input <input_dir> --output <output_dir>")
        sys.exit(1)

    errors = validate_args(args)
    if errors:
        for error in errors:
            logger.error(error)
        sys.exit(1)

    logger.info("Backend: %s", args.backend.upper())
    logger.info("Input directory: %s", args.input)
    logger.info("Output directory: %s", args.output)
    logger.info("Target QA pairs: %s", args.num_qa_pairs)
    logger.info("Strict multi-hop verification: %s", "OFF" if args.no_strict_multihop else "ON")
    write_run_metadata(args)

    logger.info("Starting OceanGraph-R1 agent pipeline...")
    run_pipeline()
    logger.info("OceanGraph-R1 pipeline completed.")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
