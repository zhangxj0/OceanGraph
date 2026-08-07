"""
Preflight Check Module - Validates all services before pipeline execution.

Checks:
1. LLM API connectivity (text generation)
2. VLM API connectivity (vision + text)
3. Embedding model loading & inference
4. Reranker model loading & inference  
5. API key availability
6. Required directories and files

Run standalone: python preflight_check.py
Or import: from oceangraph.utils.preflight import run_preflight_checks
"""

import json
import os
import subprocess
import sys
import time
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

class CheckStatus(Enum):
    PASS = "[PASS]"
    FAIL = "[FAIL]"
    WARN = "[WARN]"
    SKIP = "[SKIP]"


_RESULT_PREFIX = "OCEANGRAPH_PREFLIGHT_RESULT="
_check_timeout_override: Optional[float] = None


@dataclass
class CheckResult:
    name: str
    status: CheckStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


def _timer(func):
    """Decorator to time check functions."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        result.duration_ms = (time.time() - start) * 1000
        return result
    return wrapper


def _run_check_in_subprocess(
    name: str,
    timeout_seconds: float | None,
    runtime_config: Optional[Dict[str, Any]] = None,
) -> CheckResult:
    """Run a local model check in a killable child interpreter."""
    if timeout_seconds is None or timeout_seconds <= 0:
        return _single_check_function(name)()

    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[2])
    environment["PYTHONPATH"] = os.pathsep.join(
        value
        for value in (source_root, environment.get("PYTHONPATH", ""))
        if value
    )
    if runtime_config:
        environment["OCEANGRAPH_PREFLIGHT_CONFIG_JSON"] = json.dumps(
            runtime_config,
            ensure_ascii=False,
            default=str,
        )
    command = [
        sys.executable,
        "-m",
        "oceangraph.utils.preflight",
        "--single-check",
        name,
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            env=environment,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Check timed out after {timeout_seconds:g} seconds",
            details={"timeout_seconds": timeout_seconds, "isolated_process": True},
            duration_ms=timeout_seconds * 1000,
        )
    except OSError as exc:
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Cannot start isolated check: {exc}",
            details={"error": str(exc), "isolated_process": True},
            duration_ms=(time.monotonic() - started) * 1000,
        )

    result_line = next(
        (
            line[len(_RESULT_PREFIX) :]
            for line in reversed(completed.stdout.splitlines())
            if line.startswith(_RESULT_PREFIX)
        ),
        None,
    )
    if completed.returncode != 0 or result_line is None:
        diagnostic = (completed.stderr or completed.stdout).strip()[-1000:]
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Isolated check failed with exit code {completed.returncode}",
            details={"error": diagnostic, "isolated_process": True},
            duration_ms=(time.monotonic() - started) * 1000,
        )
    try:
        payload = json.loads(result_line)
        return CheckResult(
            name=str(payload.get("name") or name),
            status=CheckStatus[str(payload["status"])],
            message=str(payload.get("message", "")),
            details=dict(payload.get("details") or {}),
            duration_ms=float(payload.get("duration_ms", 0.0) or 0.0),
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return CheckResult(
            name=name,
            status=CheckStatus.FAIL,
            message=f"Cannot decode isolated check result: {exc}",
            details={"isolated_process": True},
        )


def _active_preflight_timeout() -> float:
    """Return the CLI override or configured probe/model-load timeout."""
    if _check_timeout_override is not None:
        return float(_check_timeout_override)
    try:
        from oceangraph.core.config import load_config

        return float(
            (load_config().get("preflight", {}) or {}).get(
                "check_timeout_seconds", 180
            )
        )
    except Exception:
        return 180.0


# ============================================================================
# INDIVIDUAL CHECK FUNCTIONS
# ============================================================================

@_timer
def check_config() -> CheckResult:
    """Check if config.yaml can be loaded."""
    try:
        from oceangraph.core.config import load_config, get_backend_config, get_paths_config, get_embedding_config
        config = load_config()
        backend = get_backend_config()
        paths = get_paths_config()
        embed = get_embedding_config()
        
        # Use env var override if set (from CLI --output), then fall back to config
        output_dir = os.environ.get("OCEANGRAPH_OUTPUT_DIR") or paths.get('output_dir', 'UNKNOWN')
        
        return CheckResult(
            name="Configuration",
            status=CheckStatus.PASS,
            message="config.yaml loaded successfully",
            details={
                "backend": backend.get('name', 'UNKNOWN'),
                "llm_model": backend.get('llm_model', 'UNKNOWN'),
                "vlm_model": backend.get('vlm_model', 'UNKNOWN'),
                "embedding_model": embed.get('model', 'UNKNOWN'),
                "output_dir": output_dir
            }
        )
    except FileNotFoundError as e:
        return CheckResult(
            name="Configuration", 
            status=CheckStatus.FAIL,
            message=f"config.yaml not found: {e}"
        )
    except Exception as e:
        return CheckResult(
            name="Configuration",
            status=CheckStatus.FAIL,
            message=f"Failed to load config: {e}"
        )


@_timer
def check_api_key() -> CheckResult:
    """Check that every routed text-generation profile has an API key."""
    try:
        from oceangraph.core.llm import _get_model_profile

        profiles = {
            stage: _get_model_profile(stage)
            for stage in ("generation", "verification")
        }
        missing = [stage for stage, profile in profiles.items() if len(profile.api_key) <= 10]
        if not missing:
            return CheckResult(
                name="API Key",
                status=CheckStatus.PASS,
                message="API keys loaded for generation and verification routes",
                details={
                    "routes": {
                        stage: profile.model_name()
                        for stage, profile in profiles.items()
                    }
                },
            )
        return CheckResult(
            name="API Key",
            status=CheckStatus.FAIL,
            message=f"API key missing for routed stages: {', '.join(missing)}",
            details={"missing_stages": missing},
        )
    except (ImportError, RuntimeError) as e:
        return CheckResult(
            name="API Key",
            status=CheckStatus.FAIL,
            message=f"Cannot resolve routed API keys: {e}",
        )


@_timer
def check_llm_call() -> CheckResult:
    """Test the routed generation model with a minimal call."""
    try:
        from oceangraph.core.llm import call_llm_simple, get_model_route_info
        
        test_prompt = "Say 'OK' and nothing else."
        from oceangraph.core.config import load_config

        probe_ttl = float(
            (load_config().get("preflight", {}) or {}).get(
                "api_probe_cache_ttl_seconds", 3600
            )
        )
        response = call_llm_simple(
            test_prompt,
            max_retries=1,
            stage="generation",
            cache_max_age_seconds=probe_ttl,
            request_timeout_seconds=_active_preflight_timeout(),
        )
        route = get_model_route_info("generation")
        
        if response and len(response.strip()) > 0:
            return CheckResult(
                name="LLM API",
                status=CheckStatus.PASS,
                message=f"Generation call successful ({route['model']})",
                details={
                    "backend": route["backend"],
                    "model": route["model"],
                    "response_preview": response[:50] + "..." if len(response) > 50 else response
                }
            )
        else:
            return CheckResult(
                name="LLM API",
                status=CheckStatus.FAIL,
                message="LLM returned empty response",
                details={"stage": "generation"},
            )
    except Exception as e:
        return CheckResult(
            name="LLM API",
            status=CheckStatus.FAIL,
            message=f"LLM call failed: {e}",
            details={"error": str(e)}
        )


@_timer
def check_vlm_call() -> CheckResult:
    """Test the routed verifier without invoking vision in text-only mode."""
    try:
        from oceangraph.core.config import is_text_only_mode
        from oceangraph.core.llm import (
            call_llm_simple,
            call_vlm_interweaved,
            get_model_route_info,
        )

        route = get_model_route_info("verification")
        from oceangraph.core.config import load_config

        probe_ttl = float(
            (load_config().get("preflight", {}) or {}).get(
                "api_probe_cache_ttl_seconds", 3600
            )
        )
        if is_text_only_mode():
            response = call_llm_simple(
                "Say 'VERIFY OK' and nothing else.",
                max_retries=1,
                stage="verification",
                cache_max_age_seconds=probe_ttl,
                request_timeout_seconds=_active_preflight_timeout(),
            )
        else:
            response = call_vlm_interweaved(
                "Say 'VLM OK' and nothing else.",
                [{"content": "Test content", "image_path": None}],
                stage="verification",
            )
        
        if response and len(response.strip()) > 0:
            return CheckResult(
                name="Verifier API",
                status=CheckStatus.PASS,
                message=f"Verification call successful ({route['model']})",
                details={
                    "backend": route["backend"],
                    "model": route["model"],
                    "response_preview": response[:50] + "..." if len(response) > 50 else response
                }
            )
        else:
            return CheckResult(
                name="Verifier API",
                status=CheckStatus.FAIL,
                message="Verifier returned empty response",
                details={"stage": "verification"},
            )
    except Exception as e:
        return CheckResult(
            name="Verifier API",
            status=CheckStatus.FAIL,
            message=f"Verification call failed: {e}",
            details={"error": str(e)}
        )


@_timer  
def check_embedding_model() -> CheckResult:
    """Test embedding model loading and inference."""
    try:
        import os
        from oceangraph.core.config import get_embedding_config
        embed_config = get_embedding_config()
        # Check environment variable override first (used by demo)
        model_name = os.environ.get("OCEANGRAPH_EMBEDDING_MODEL") or embed_config.get('model', 'bge_m3')
        
        test_text = "This is a test sentence for embedding."
        
        # Handle Gemini API-based embeddings (no local GPU required)
        if model_name in ["gemini", "gemini-embedding-001"]:
            from oceangraph.core.config import get_backend_config
            backend_config = get_backend_config()
            api_key = os.environ.get("GEMINI_API_KEY") or backend_config.get("gemini", {}).get("api_key")
            if not api_key:
                return CheckResult(
                    name="Embedding Model",
                    status=CheckStatus.FAIL,
                    message="Gemini API key required for Gemini embeddings",
                    details={"model": model_name}
                )
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=test_text,
                task_type="retrieval_document"
            )
            embedding = result['embedding']
            return CheckResult(
                name="Embedding Model",
                status=CheckStatus.PASS,
                message="Gemini API embeddings working",
                details={"model": "gemini-text-embedding-004", "embedding_dim": len(embedding)}
            )
        
        # Handle "auto" or "multimodal" - use fallback logic
        elif model_name in ["auto", "multimodal", "", None]:
            from oceangraph.embeddings.models import get_multimodal_embedder
            gpus = embed_config.get('gpus', None)
            embedder, actual_model, is_multimodal = get_multimodal_embedder(gpus=gpus)
            model_display = f"{actual_model} (multimodal={is_multimodal})"
            # Use encode() which all embedders support
            embedding = embedder.encode(test_text, convert_to_numpy=True)
        elif model_name == "qwen3_vl":
            from oceangraph.embeddings.models import Qwen3VLEmbed
            gpus = embed_config.get('gpus', None)
            embedder = Qwen3VLEmbed(gpus=gpus)
            model_display = "Qwen3-VL Multimodal"
            embedding = embedder.embed_text(test_text)
            if hasattr(embedding, 'cpu'):
                embedding = embedding.cpu().float().numpy()
        elif model_name in ["nomic", "nomic-ai/nomic-embed-multimodal-7b"]:
            from oceangraph.embeddings.models import NomicVLEmbed
            gpus = embed_config.get('gpus', None)
            embedder = NomicVLEmbed(gpus=gpus)
            model_display = "Nomic Multimodal"
            embedding = embedder.embed_text(test_text)
            if hasattr(embedding, 'cpu'):
                embedding = embedding.cpu().float().numpy()
        elif model_name in ["bge_m3", "BAAI/bge-m3"]:
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer("BAAI/bge-m3", trust_remote_code=True)
            model_display = "BAAI/bge-m3"
            embedding = embedder.encode(test_text, convert_to_numpy=True)
        else:
            from sentence_transformers import SentenceTransformer
            embedder = SentenceTransformer(model_name, trust_remote_code=True)
            model_display = model_name
            embedding = embedder.encode(test_text, convert_to_numpy=True)
        
        if embedding is not None and len(embedding) > 0:
            dim = len(embedding) if hasattr(embedding, '__len__') else embedding.shape[-1]
            return CheckResult(
                name="Embedding Model",
                status=CheckStatus.PASS,
                message=f"Embedding model loaded and working",
                details={
                    "model": model_display,
                    "config_name": model_name,
                    "embedding_dim": dim
                }
            )
        else:
            return CheckResult(
                name="Embedding Model",
                status=CheckStatus.FAIL,
                message="Embedding returned empty result",
                details={"model": model_display}
            )
    except ImportError as e:
        return CheckResult(
            name="Embedding Model",
            status=CheckStatus.FAIL,
            message=f"Cannot import embedding module: {e}",
            details={"error": str(e)}
        )
    except Exception as e:
        return CheckResult(
            name="Embedding Model",
            status=CheckStatus.FAIL,
            message=f"Embedding model failed: {e}",
            details={"error": str(e)}
        )


@_timer
def check_reranker() -> CheckResult:
    """Test reranker model loading."""
    try:
        from oceangraph.core.config import load_config
        config = load_config()
        reranker_config = config.get('reranker', {})
        default_reranker = reranker_config.get('default', 'gemini_vlm')
        
        if default_reranker == "gemini_vlm":
            # Gemini VLM reranker uses API, already tested in VLM check
            # Get actual model name from config
            try:
                from oceangraph.core.llm import VLM_MODEL_NAME, _initialize_config
                _initialize_config()
                model_name = VLM_MODEL_NAME if VLM_MODEL_NAME else "gemini-2.0-flash"
            except:
                model_name = "gemini-2.0-flash"
            return CheckResult(
                name="Reranker",
                status=CheckStatus.PASS,
                message="Using Gemini VLM reranker (API-based)",
                details={"type": "gemini_vlm", "model": model_name}
            )
        elif default_reranker in ["monovlm", "MonoVLM"]:
            from oceangraph.embeddings.rerankers import MonoVLMReranker
            reranker = MonoVLMReranker()
            
            # Test with minimal query
            test_query = "test query"
            test_chunks = [{"content": "test content", "chunk_id": "1"}]
            rankings = reranker.rerank(test_query, test_chunks, top_k=1)
            
            return CheckResult(
                name="Reranker",
                status=CheckStatus.PASS,
                message="MonoVLM reranker loaded and working",
                details={"type": "monovlm", "model": "lightonai/MonoQwen2-VL-v0.1"}
            )
        elif default_reranker in ["text_embedding", "text-embedding"]:
            from oceangraph.embeddings.rerankers import TextEmbeddingReranker
            reranker = TextEmbeddingReranker()

            test_query = "ocean heat content"
            test_chunks = [{"text": "Ocean heat content records changes in stored ocean energy.", "chunk_id": "1"}]
            rankings = reranker.rerank(test_query, test_chunks, top_k=1)

            if rankings:
                return CheckResult(
                    name="Reranker",
                    status=CheckStatus.PASS,
                    message="Text embedding reranker loaded and working",
                    details={"type": "text_embedding", "model": "BAAI/bge-large-en-v1.5"}
                )
            return CheckResult(
                name="Reranker",
                status=CheckStatus.FAIL,
                message="Text embedding reranker returned no rankings",
                details={"type": "text_embedding"}
            )
        else:
            return CheckResult(
                name="Reranker",
                status=CheckStatus.WARN,
                message=f"Unknown reranker type: {default_reranker}",
                details={"type": default_reranker}
            )
    except Exception as e:
        return CheckResult(
            name="Reranker",
            status=CheckStatus.FAIL,
            message=f"Reranker check failed: {e}",
            details={"error": str(e)}
        )


@_timer
def check_metrics_embeddings() -> CheckResult:
    """Test metrics evaluation embeddings (for answer_relevancy and semantic_diversity)."""
    try:
        from oceangraph.evaluation.metrics import (
            LocalEmbeddingWrapper,
            SENTENCE_TRANSFORMERS_AVAILABLE,
        )

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return CheckResult(
                name="Metrics Embeddings",
                status=CheckStatus.FAIL,
                message="sentence-transformers is required for BGE-M3 evaluation embeddings",
                details={"backend": "local"},
            )

        embeddings = LocalEmbeddingWrapper("BAAI/bge-m3")
        test_emb = embeddings.embed_query("test")
        return CheckResult(
            name="Metrics Embeddings",
            status=CheckStatus.PASS,
            message="Using local BGE-M3 embeddings for metrics",
            details={"backend": "sentence-transformers", "model": "BAAI/bge-m3", "dim": len(test_emb)},
        )
    except Exception as e:
        return CheckResult(
            name="Metrics Embeddings",
            status=CheckStatus.FAIL,
            message=f"Metrics embeddings check failed: {e}",
            details={"error": str(e)}
        )


@_timer
def check_gpu_availability() -> CheckResult:
    """Check GPU availability and memory."""
    try:
        import torch
        
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            gpus = []
            for i in range(gpu_count):
                props = torch.cuda.get_device_properties(i)
                free_mem = torch.cuda.memory_reserved(i) - torch.cuda.memory_allocated(i)
                total_mem = props.total_memory / (1024**3)
                gpus.append({
                    "id": i,
                    "name": props.name,
                    "total_gb": round(total_mem, 1)
                })
            
            return CheckResult(
                name="GPU",
                status=CheckStatus.PASS,
                message=f"Found {gpu_count} GPU(s)",
                details={"gpus": gpus}
            )
        else:
            return CheckResult(
                name="GPU",
                status=CheckStatus.WARN,
                message="No GPU available, will use CPU (slower)",
                details={}
            )
    except ImportError:
        return CheckResult(
            name="GPU",
            status=CheckStatus.WARN,
            message="PyTorch not available for GPU check",
            details={}
        )
    except Exception as e:
        return CheckResult(
            name="GPU",
            status=CheckStatus.WARN,
            message=f"GPU check error: {e}",
            details={"error": str(e)}
        )


@_timer
def check_output_directory() -> CheckResult:
    """Check if output directory is writable."""
    try:
        from oceangraph.core.config import get_paths_config
        paths = get_paths_config()
        
        # Use env var override if set (from CLI --output), then fall back to config
        output_dir = os.environ.get("OCEANGRAPH_OUTPUT_DIR") or paths.get('output_dir', 'trials/results')
        
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Test write
        test_file = os.path.join(output_dir, ".preflight_test")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        
        return CheckResult(
            name="Output Directory",
            status=CheckStatus.PASS,
            message=f"Output directory writable",
            details={"path": output_dir}
        )
    except Exception as e:
        return CheckResult(
            name="Output Directory",
            status=CheckStatus.FAIL,
            message=f"Cannot write to output directory: {e}",
            details={"error": str(e)}
        )


# Module-level override for input directory (set before running checks)
_input_dir_override: Optional[str] = None

@_timer
def check_input_data() -> CheckResult:
    """Check if input data exists."""
    try:
        from oceangraph.core.config import get_paths_config
        paths = get_paths_config()

        output_dir = os.environ.get("OCEANGRAPH_OUTPUT_DIR") or paths.get("output_dir")
        output_chunks = Path(output_dir) / "chunks.json" if output_dir else None
        if output_chunks and output_chunks.exists():
            with output_chunks.open("r", encoding="utf-8") as handle:
                chunks = json.load(handle)
            return CheckResult(
                name="Input Data",
                status=CheckStatus.PASS,
                message=f"Found resumable output with {len(chunks)} chunks",
                details={"source": "output_checkpoint", "path": str(output_chunks), "count": len(chunks)},
            )

        # Use override if set, then check environment variable, then use config
        input_pdf_dir = _input_dir_override or os.environ.get("OCEANGRAPH_INPUT_DIR") or paths.get('input_pdf_dir')
        input_chunks_file = paths.get('input_chunks_file')
        
        if input_chunks_file and os.path.exists(input_chunks_file):
            with open(input_chunks_file, 'r') as f:
                chunks = json.load(f)
            return CheckResult(
                name="Input Data",
                status=CheckStatus.PASS,
                message=f"Found pre-chunked data with {len(chunks)} chunks",
                details={"source": "chunks_file", "path": input_chunks_file, "count": len(chunks)}
            )
        
        if input_pdf_dir and os.path.exists(input_pdf_dir):
            # Match the engine's recursive source discovery so a nested archive
            # layout cannot pass one stage and fail the other.
            from oceangraph.utils.sources import (
                count_source_types,
                discover_source_documents,
            )

            documents = discover_source_documents(
                input_pdf_dir,
                require_unique_stems=True,
            )
            counts = count_source_types(documents)
            total_files = len(documents)
            
            if total_files > 0:
                file_types = []
                if counts["pdf"]:
                    file_types.append(f"{counts['pdf']} PDF")
                if counts["html"]:
                    file_types.append(f"{counts['html']} HTML")
                if counts["text"]:
                    file_types.append(f"{counts['text']} text/Markdown")
                return CheckResult(
                    name="Input Data",
                    status=CheckStatus.PASS,
                    message=f"Found {', '.join(file_types)} files",
                    details={"source": "input_dir", "path": input_pdf_dir, "count": total_files}
                )
            else:
                return CheckResult(
                    name="Input Data",
                    status=CheckStatus.FAIL,
                    message="No PDF, HTML, text, or Markdown files in input directory",
                    details={"path": input_pdf_dir}
                )
        
        return CheckResult(
            name="Input Data",
            status=CheckStatus.FAIL,
            message="No input data configured",
            details={}
        )
    except Exception as e:
        return CheckResult(
            name="Input Data",
            status=CheckStatus.FAIL,
            message=f"Input data check failed: {e}",
            details={"error": str(e)}
        )


# ============================================================================
# MAIN PREFLIGHT CHECK RUNNER
# ============================================================================


_ISOLATED_CHECK_FUNCTIONS = {
    "embedding": check_embedding_model,
    "reranker": check_reranker,
    "metrics_emb": check_metrics_embeddings,
}


def _single_check_function(name: str):
    """Resolve a local model check by its stable subprocess name."""
    try:
        return _ISOLATED_CHECK_FUNCTIONS[name]
    except KeyError as exc:
        raise ValueError(f"Unknown isolated preflight check: {name}") from exc


def run_preflight_checks(
    skip_expensive: bool = False,
    quiet: bool = False,
    input_dir: Optional[str] = None,
    check_timeout_seconds: Optional[float] = None,
) -> Tuple[bool, List[CheckResult]]:
    """
    Run all preflight checks.
    
    Args:
        skip_expensive: Skip model loading checks (LLM, VLM, embedding, reranker)
        quiet: Suppress output
        input_dir: Override input directory for check (uses config.yaml if None)
        check_timeout_seconds: Maximum wait for each expensive check. ``None``
            loads ``preflight.check_timeout_seconds`` (default: 180 seconds).
    
    Returns:
        Tuple of (all_passed: bool, results: List[CheckResult])
    """
    global _input_dir_override, _check_timeout_override
    _input_dir_override = input_dir
    
    results = []

    try:
        from oceangraph.core.config import load_config

        active_config = load_config()
    except Exception:
        active_config = {}
    preflight_config = active_config.get("preflight", {}) or {}
    if check_timeout_seconds is None:
        check_timeout_seconds = float(
            preflight_config.get("check_timeout_seconds", 180)
        )
    previous_timeout_override = _check_timeout_override
    _check_timeout_override = check_timeout_seconds
    evaluation_enabled = bool(
        (active_config.get("evaluation", {}) or {}).get("run_evaluation", False)
    )
    if os.environ.get("OCEANGRAPH_RUN_EVALUATION") is not None:
        evaluation_enabled = os.environ["OCEANGRAPH_RUN_EVALUATION"] == "1"
    
    # Define checks in order of importance
    checks = [
        ("config", check_config, False),
        ("api_key", check_api_key, False),
        ("input_data", check_input_data, False),
        ("output_dir", check_output_directory, False),
        ("gpu", check_gpu_availability, False),
        ("llm", check_llm_call, True),
        ("vlm", check_vlm_call, True),
        ("embedding", check_embedding_model, True),
        ("reranker", check_reranker, True),
        ("metrics_emb", check_metrics_embeddings, True),
    ]
    
    if not quiet:
        print("\n" + "=" * 70)
        print("PREFLIGHT CHECKS - Validating all services before execution")
        print("=" * 70 + "\n")
    
    prerequisite_failed = False
    expensive_failed = False
    isolated_checks = {"embedding", "reranker", "metrics_emb"}
    for name, check_func, is_expensive in checks:
        if name == "metrics_emb" and not evaluation_enabled:
            result = CheckResult(
                name="Metrics Embeddings",
                status=CheckStatus.SKIP,
                message="Skipped because evaluation.run_evaluation is false",
            )
        elif is_expensive and skip_expensive:
            result = CheckResult(
                name=name.upper(),
                status=CheckStatus.SKIP,
                message="Skipped (--skip-expensive)"
            )
        elif is_expensive and prerequisite_failed:
            result = CheckResult(
                name=name.upper(),
                status=CheckStatus.SKIP,
                message="Skipped because a mandatory local prerequisite failed",
            )
        elif is_expensive and expensive_failed:
            result = CheckResult(
                name=name.upper(),
                status=CheckStatus.SKIP,
                message="Skipped after an earlier expensive check failed",
            )
        else:
            if not quiet:
                print(f"  Checking {name}...", end=" ", flush=True)
            if (
                name in isolated_checks
                and check_func is _ISOLATED_CHECK_FUNCTIONS[name]
            ):
                result = _run_check_in_subprocess(
                    name,
                    check_timeout_seconds,
                    runtime_config=active_config,
                )
            else:
                result = check_func()
            if not quiet:
                print(f"{result.status.value} ({result.duration_ms:.0f}ms)")
        
        results.append(result)
        if result.status == CheckStatus.FAIL:
            if is_expensive:
                expensive_failed = True
            else:
                prerequisite_failed = True

    _check_timeout_override = previous_timeout_override
    
    # Count results
    passed = sum(1 for r in results if r.status == CheckStatus.PASS)
    failed = sum(1 for r in results if r.status == CheckStatus.FAIL)
    warned = sum(1 for r in results if r.status == CheckStatus.WARN)
    skipped = sum(1 for r in results if r.status == CheckStatus.SKIP)
    
    all_passed = failed == 0
    
    if not quiet:
        print("\n" + "=" * 70)
        print("PREFLIGHT CHECK SUMMARY")
        print("=" * 70)
        print(f"\n  Results: {passed} passed, {failed} failed, {warned} warnings, {skipped} skipped\n")
        
        # Print detailed report
        print("  " + "-" * 66)
        print(f"  {'Service':<25} {'Status':<12} {'Details':<30}")
        print("  " + "-" * 66)
        
        for result in results:
            status_str = result.status.value.split()[0]  # Just the emoji
            details_str = ""
            
            if result.details:
                if 'model' in result.details:
                    details_str = result.details['model']
                elif 'backend' in result.details:
                    details_str = result.details['backend']
                elif 'path' in result.details:
                    details_str = os.path.basename(str(result.details['path']))
                elif 'count' in result.details:
                    details_str = f"{result.details['count']} items"
            
            print(f"  {result.name:<25} {status_str:<12} {details_str:<30}")
        
        print("  " + "-" * 66)
        
        # Configuration summary
        config_result = next((r for r in results if r.name == "Configuration"), None)
        if config_result and config_result.status == CheckStatus.PASS:
            d = config_result.details
            print(f"\n  Active Configuration:")
            print(f"     - Backend:    {d.get('backend', 'N/A')}")
            print(f"     - LLM Model:  {d.get('llm_model', 'N/A')}")
            print(f"     - VLM Model:  {d.get('vlm_model', 'N/A')}")
            print(f"     - Embeddings: {d.get('embedding_model', 'N/A')}")
            print(f"     - Output Dir: {d.get('output_dir', 'N/A')}")
        
        print("\n" + "=" * 70)
        
        if all_passed:
            print("[OK] ALL CHECKS PASSED - Ready to start pipeline execution")
        else:
            print("[FAIL] PREFLIGHT CHECKS FAILED - Fix issues before proceeding")
            print("\n   Failed checks:")
            for result in results:
                if result.status == CheckStatus.FAIL:
                    print(f"   - {result.name}: {result.message}")
        
        print("=" * 70 + "\n")
    
    return all_passed, results


def require_preflight_checks() -> bool:
    """Run preflight checks and exit if any fail. Returns True if all pass."""
    all_passed, results = run_preflight_checks()
    
    if not all_passed:
        print("\nSTOPPING: Preflight checks failed. Fix the issues above before running the pipeline.")
        print("   This prevents wasted LLM API calls on a misconfigured system.\n")
        sys.exit(1)
    
    return True


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

def main():
    """Main entry point for preflight checks CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run preflight checks for QA pipeline")
    parser.add_argument("--skip-expensive", action="store_true", 
                       help="Skip expensive checks (model loading, API calls)")
    parser.add_argument("--quiet", action="store_true",
                       help="Suppress output")
    parser.add_argument("--timeout", type=float, default=None,
                        help="Per-check timeout in seconds")
    parser.add_argument(
        "--single-check",
        choices=("embedding", "reranker", "metrics_emb"),
        default=None,
        help=argparse.SUPPRESS,
    )
    
    args = parser.parse_args()

    if args.single_check:
        runtime_config_json = os.environ.pop(
            "OCEANGRAPH_PREFLIGHT_CONFIG_JSON",
            "",
        )
        if runtime_config_json:
            from oceangraph.core.config import set_runtime_config

            set_runtime_config(json.loads(runtime_config_json))
        result = _single_check_function(args.single_check)()
        print(
            _RESULT_PREFIX
            + json.dumps(
                {
                    "name": result.name,
                    "status": result.status.name,
                    "message": result.message,
                    "details": result.details,
                    "duration_ms": result.duration_ms,
                },
                ensure_ascii=False,
                default=str,
            )
        )
        sys.exit(0)
    
    all_passed, _ = run_preflight_checks(
        skip_expensive=args.skip_expensive,
        quiet=args.quiet,
        check_timeout_seconds=args.timeout,
    )
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

