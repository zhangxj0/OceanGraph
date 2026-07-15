#!/usr/bin/env python3
"""Run one OceanGraph-R1 domain dataset generation pipeline."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class OceanDomain:
    slug: str
    title: str
    short_name: str
    domain: str
    expert_persona: str
    default_input: str
    description: str
    recommended_sources: list[str]
    question_focus: list[str]


DOMAINS: dict[str, OceanDomain] = {
    "physical_ocean_climate": OceanDomain(
        slug="physical_ocean_climate",
        title="Physical Oceanography and Climate Dynamics",
        short_name="physical-climate",
        domain="Physical Oceanography and Climate-Ocean Dynamics",
        expert_persona="Physical Oceanography Multi-Hop QA Curator",
        default_input="data/ocean_physical_climate",
        description=(
            "Large-scale circulation, air-sea interaction, sea level, ocean heat content, "
            "ENSO, marine heatwaves, and other climate-linked physical processes."
        ),
        recommended_sources=[
            "NOAA climate/ocean explainers and technical reports",
            "IPCC ocean and cryosphere chapters",
            "Argo and ocean heat content documentation",
            "Regional circulation or marine heatwave papers",
        ],
        question_focus=["causal", "temporal", "spatial", "comparison"],
    ),
    "carbon_biogeochemistry": OceanDomain(
        slug="carbon_biogeochemistry",
        title="Ocean Carbon Cycle and Marine Biogeochemistry",
        short_name="carbon-biogeochemistry",
        domain="Ocean Carbon Cycle and Marine Biogeochemistry",
        expert_persona="Ocean Carbon Cycle Multi-Hop QA Curator",
        default_input="data/ocean_carbon_biogeochemistry",
        description=(
            "Biological pump, solubility pump, ocean acidification, nutrients, dissolved oxygen, "
            "hypoxia, remineralization, and carbon storage pathways."
        ),
        recommended_sources=[
            "NOAA ocean acidification material",
            "NASA/NOAA carbon cycle reports",
            "Biogeochemical Argo documentation",
            "Peer-reviewed biological pump and deoxygenation papers",
        ],
        question_focus=["bridge", "causal", "mechanism", "numeric"],
    ),
    "remote_sensing_observing": OceanDomain(
        slug="remote_sensing_observing",
        title="Ocean Remote Sensing and Observing Systems",
        short_name="remote-observing",
        domain="Ocean Remote Sensing and Observing Systems",
        expert_persona="Ocean Observing Systems Multi-Hop QA Curator",
        default_input="data/ocean_remote_sensing_observing",
        description=(
            "SST, SSH, ocean color, chlorophyll, salinity, Argo, buoys, gliders, satellites, "
            "retrieval variables, validation, and observing network design."
        ),
        recommended_sources=[
            "NASA Ocean Color and Earthdata documentation",
            "NOAA CoastWatch product guides",
            "GOOS Essential Ocean Variables pages",
            "Argo, drifter, glider, and buoy technical documentation",
        ],
        question_focus=["variable-to-instrument", "comparison", "spatial", "retrieval"],
    ),
    "marine_ecology_fisheries": OceanDomain(
        slug="marine_ecology_fisheries",
        title="Marine Ecology, Ecosystems, and Fisheries",
        short_name="ecology-fisheries",
        domain="Marine Ecology, Ecosystem Response, and Fisheries Oceanography",
        expert_persona="Marine Ecosystem Multi-Hop QA Curator",
        default_input="data/ocean_marine_ecology_fisheries",
        description=(
            "Primary productivity, plankton blooms, coral bleaching, food webs, fisheries habitat, "
            "ecosystem indicators, and biological response to physical or chemical drivers."
        ),
        recommended_sources=[
            "NOAA fisheries ecosystem reports",
            "Marine heatwave and coral bleaching reports",
            "Regional ecosystem status reports",
            "Peer-reviewed plankton, habitat, and food-web papers",
        ],
        question_focus=["ecosystem-response", "bridge", "causal", "comparison"],
    ),
    "coastal_hazards_human": OceanDomain(
        slug="coastal_hazards_human",
        title="Coastal Hazards and Human Impacts",
        short_name="coastal-hazards",
        domain="Coastal Ocean Hazards, Pollution, and Human Impacts",
        expert_persona="Coastal Ocean Hazards Multi-Hop QA Curator",
        default_input="data/ocean_coastal_hazards_human",
        description=(
            "Storm surge, coastal flooding, harmful algal blooms, eutrophication, pollution, "
            "marine debris, shoreline change, and management-relevant ocean risk."
        ),
        recommended_sources=[
            "NOAA coastal hazard and storm surge reports",
            "Harmful algal bloom and hypoxia reports",
            "Coastal pollution and marine debris reports",
            "Regional coastal resilience or management documents",
        ],
        question_focus=["risk-chain", "causal", "spatial", "policy-evidence"],
    ),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def build_config(args: argparse.Namespace, domain: OceanDomain) -> dict[str, Any]:
    backend = args.backend.upper()
    backend_lower = backend.lower()
    return {
        "framework": {
            "name": "OceanGraph-R1",
            "description": "Domain-aware multi-agent generation for ocean science multi-hop QA datasets",
            "agents": [
                "domain_corpus",
                "evidence_reasoning",
                "qa_verification",
            ],
        },
        "pipeline": {"modality": "text"},
        "backend": {
            "active": backend,
            "openai": {
                "url": args.api_url,
                "api_key_path": "",
                "llm_model": args.llm_model,
                "vlm_model": args.vlm_model,
                "timeout": 300,
            },
            "gemini": {
                "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                "api_key_path": "",
                "llm_model": args.llm_model if backend_lower == "gemini" else "gemini-2.0-flash",
                "vlm_model": args.vlm_model if backend_lower == "gemini" else "gemini-2.0-flash",
                "timeout": 300,
            },
            "ollama": {
                "url": args.ollama_url,
                "llm_model": args.llm_model if backend_lower == "ollama" else "llama3.1:8b",
                "vlm_model": args.vlm_model if backend_lower == "ollama" else "llava:13b",
                "num_ctx": 16384,
                "temperature": 0.0,
                "stream": False,
            },
        },
        "models": {
            "profiles": {
                "generator": {
                    "backend": backend,
                    "url": args.api_url if backend_lower == "openai" else "",
                    "api_key_env": "OPENAI_API_KEY" if backend_lower == "openai" else "GEMINI_API_KEY",
                    "model": args.llm_model,
                    "supports_vision": False,
                    "temperature": 0.0,
                    "structured_output": backend_lower == "openai",
                    "timeout": 300,
                },
                "verifier": {
                    "backend": backend,
                    "url": args.api_url if backend_lower == "openai" else "",
                    "api_key_env": "OPENAI_API_KEY" if backend_lower == "openai" else "GEMINI_API_KEY",
                    "model": args.llm_model,
                    "supports_vision": False,
                    "temperature": 0.0,
                    "structured_output": backend_lower == "openai",
                    "timeout": 300,
                },
            },
            "stages": {
                "corpus": "generator",
                "retrieval": "generator",
                "generation": "generator",
                "selection": "verifier",
                "verification": "verifier",
                "correction": "generator",
            },
        },
        "rate_limiting": {
            "requests_per_minute": args.requests_per_minute,
            "burst_size": args.burst_size,
        },
        "paths": {
            "input_pdf_dir": str(args.input),
            "input_chunks_file": None,
            "output_dir": str(args.output),
        },
        "processing": {
            "max_pdfs": None,
            "sort_by_size": True,
            "max_chunks": args.max_chunks,
        },
        "parallel": {
            "num_workers": args.max_workers,
            "available_gpus": [0],
            "qa_max_workers": args.max_workers,
            "dedup_max_workers": max(1, args.max_workers),
        },
        "embedding": {
            "model": args.embedding_model,
            "cache_embeddings": True,
            "local_files_only": args.offline_models,
            "batch_size": args.embed_batch_size,
        },
        "reranker": {"default": args.reranker_model},
        "retrieval": {
            "multihop": {
                "max_depth": args.max_depth,
                "max_breadth": args.max_breadth,
                "chunks_per_search": args.chunks_per_search,
                "chunk_addition_mode": args.chunk_addition_mode,
            }
        },
        "qa_generation": {
            "num_qa_pairs": args.num_qa_pairs,
            "type": args.qa_type,
            "strict_multihop_verification": not args.relaxed,
            "min_supporting_chunks": args.min_supporting_chunks,
            "output_jsonl": True,
            "counterfactual_verification": True,
        },
        "qa_correction": {"enabled": True, "max_attempts": 1},
        "deduplication": {"enabled": args.deduplication},
        "evaluation": {"run_evaluation": args.evaluation, "sample_size": None},
        "faiss": {
            "index_type": "IndexFlatIP",
            "normalize_l2": True,
            "use_gpu": False,
            "gpu_id": 0,
        },
        "shuffling": {"enabled": True, "seed": args.shuffle_seed},
        "domain_expert": {
            "domain": domain.domain,
            "expert_persona": domain.expert_persona,
            "use_multimodal_embeddings": False,
            "output_dir": str(args.output / "domain_analysis"),
        },
    }


def write_config(path: Path, config: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")


def count_input_files(input_dir: Path) -> int:
    if not input_dir.exists():
        return 0
    allowed = {".pdf", ".html", ".htm", ".txt", ".md", ".markdown"}
    ignored_names = {"README.md", ".gitkeep"}
    return sum(
        1
        for path in input_dir.rglob("*")
        if path.is_file()
        and path.name not in ignored_names
        and path.suffix.lower() in allowed
    )


def write_input_readme(input_dir: Path, domain: OceanDomain) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    readme = input_dir / "README.md"
    if readme.exists():
        return
    lines = [
        f"# {domain.title}",
        "",
        domain.description,
        "",
        "Put PDF, HTML, TXT, or Markdown source documents in this directory before running the dataset script.",
        "",
        "Recommended source types:",
        *[f"- {item}" for item in domain.recommended_sources],
        "",
        "Question focus:",
        *[f"- {item}" for item in domain.question_focus],
        "",
    ]
    readme.write_text("\n".join(lines), encoding="utf-8")


def run_command(cmd: list[str], env: dict[str, str], cwd: Path, dry_run: bool) -> None:
    print("\n$ " + " ".join(str(part) for part in cmd))
    if dry_run:
        return
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def parse_args(default_domain: str | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--domain", choices=sorted(DOMAINS), default=default_domain)
    parser.add_argument("--input", type=Path, help="Input document directory")
    parser.add_argument("--output", type=Path, help="OceanGraph framework output directory")
    parser.add_argument("--num-qa-pairs", type=int, default=env_int("OCEAN_NUM_QA_PAIRS", 200))
    parser.add_argument("--backend", choices=["openai", "gemini", "ollama"], default=os.environ.get("OCEAN_BACKEND", "openai"))
    parser.add_argument("--api-url", default=os.environ.get("OCEAN_API_URL", "https://api.deepseek.com/chat/completions"))
    parser.add_argument("--ollama-url", default=os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434/api/chat"))
    parser.add_argument("--llm-model", default=os.environ.get("OCEAN_LLM_MODEL", "deepseek-chat"))
    parser.add_argument("--embedding-model", default=os.environ.get("OCEAN_EMBEDDING_MODEL", "bge_m3"))
    parser.add_argument("--offline-models", action="store_true", help="Use only locally cached Hugging Face models")
    parser.add_argument("--reranker-model", default=os.environ.get("OCEAN_RERANKER_MODEL", "text_embedding"))
    parser.add_argument(
        "--qa-type",
        choices=["multihop", "text"],
        default=os.environ.get("OCEAN_QA_TYPE", "multihop"),
        help="Generate text-only multi-hop or text QA records",
    )
    parser.add_argument("--max-workers", type=int, default=env_int("OCEAN_MAX_WORKERS", 1))
    parser.add_argument("--embed-batch-size", type=int, default=env_int("OCEAN_EMBED_BATCH_SIZE", 8))
    parser.add_argument("--max-depth", type=int, default=env_int("OCEAN_MAX_DEPTH", 3))
    parser.add_argument("--max-breadth", type=int, default=env_int("OCEAN_MAX_BREADTH", 4))
    parser.add_argument("--chunks-per-search", type=int, default=env_int("OCEAN_CHUNKS_PER_SEARCH", 3))
    parser.add_argument("--min-supporting-chunks", type=int, default=env_int("OCEAN_MIN_SUPPORTING_CHUNKS", 2))
    parser.add_argument("--chunk-addition-mode", choices=["RELATED", "EXPLANATORY"], default=os.environ.get("OCEAN_CHUNK_ADDITION_MODE", "RELATED"))
    parser.add_argument("--requests-per-minute", type=int, default=env_int("OCEAN_RPM", 60))
    parser.add_argument("--burst-size", type=int, default=env_int("OCEAN_BURST", 15))
    parser.add_argument("--shuffle-seed", type=int, default=env_int("OCEAN_SHUFFLE_SEED", 42))
    parser.add_argument("--max-chunks", type=int, default=None)
    parser.add_argument("--hf-endpoint", default=os.environ.get("HF_ENDPOINT", ""))
    parser.add_argument("--relaxed", action="store_true", help="Disable strict single-chunk shortcut verification")
    parser.add_argument("--deduplication", action="store_true")
    parser.add_argument("--evaluation", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--init-input-dir", action="store_true", help="Create the input directory README and exit")
    args = parser.parse_args()
    if not args.domain:
        parser.error("--domain is required when calling ocean_dataset_runner.py directly")
    return args


def main(default_domain: str | None = None) -> int:
    args = parse_args(default_domain)
    root = repo_root()
    domain = DOMAINS[args.domain]

    args.input = (args.input or root / domain.default_input).resolve()
    args.output = (args.output or root / "output" / f"oceangraph_{domain.slug}").resolve()
    write_input_readme(args.input, domain)
    if args.init_input_dir:
        print(f"Initialized input directory: {args.input}")
        return 0

    file_count = count_input_files(args.input)
    if file_count == 0:
        print(f"[ERROR] No source documents found in {args.input}")
        print("        Add PDF/HTML/TXT/Markdown files there, or pass --input <dir>.")
        print("        Use --init-input-dir to only create the directory template.")
        return 2

    args.output.mkdir(parents=True, exist_ok=True)
    config_path = args.output / "oceangraph_domain_config.yaml"
    config = build_config(args, domain)
    write_config(config_path, config)

    manifest = {
        "framework": {
            "name": "OceanGraph-R1",
            "version": "0.1.0",
            "task": "ocean science evidence-grounded multi-hop search reasoning",
        },
        "domain": asdict(domain),
        "input": str(args.input),
        "output": str(args.output),
        "num_input_files": file_count,
        "num_qa_pairs": args.num_qa_pairs,
        "qa_type": args.qa_type,
        "strict_multihop": not args.relaxed,
        "offline_models": args.offline_models,
    }
    (args.output / "oceangraph_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    env = os.environ.copy()
    env["OCEANGRAPH_CONFIG"] = str(config_path)
    env["DATASET_DOMAIN"] = domain.domain
    env["DATASET_EXPERT_PERSONA"] = domain.expert_persona
    env["OCEANGRAPH_BACKEND"] = args.backend.upper()
    env["LLM_BACKEND"] = args.backend.upper()
    if args.hf_endpoint:
        env["HF_ENDPOINT"] = args.hf_endpoint
    if args.offline_models:
        env["OCEANGRAPH_OFFLINE_MODELS"] = "1"

    python = Path(os.environ.get("OCEANGRAPH_PYTHON", sys.executable))

    framework_cmd = [
        str(python),
        "run_oceangraph.py",
        "--config",
        str(config_path),
        "--input",
        str(args.input),
        "--output",
        str(args.output),
        "--backend",
        args.backend,
        "--model",
        args.llm_model,
        "--embedding-model",
        args.embedding_model,
        "--reranker-model",
        args.reranker_model,
        "--num-qa-pairs",
        str(args.num_qa_pairs),
        "--max-workers",
        str(args.max_workers),
        "--max-depth",
        str(args.max_depth),
        "--min-supporting-chunks",
        str(args.min_supporting_chunks),
    ]
    if args.relaxed:
        framework_cmd.append("--no-strict-multihop")
    if args.offline_models:
        framework_cmd.append("--offline-models")
    if args.deduplication:
        framework_cmd.append("--deduplication")
    if args.evaluation:
        framework_cmd.append("--evaluation")
    run_command(framework_cmd, env, root, args.dry_run)

    print("\nDone.")
    print(f"OceanGraph output: {args.output}")
    print("Dataset generation complete. Optional format conversion can be run separately when needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
