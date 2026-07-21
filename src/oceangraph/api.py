"""
OceanGraph High-Level Python API

A clean, library-style interface for OceanGraph — designed to feel like
HuggingFace Transformers, OpenAI, or scikit-learn.

===========================================================================
Quick Start:
===========================================================================

    from oceangraph import OceanGraph

    pipeline = OceanGraph(
        input_dir="data/my_documents",
        output_dir="output/results",
        backend="gemini",
        api_key="your-api-key",
    )
    results = pipeline.run()
    results.save("my_dataset.json")

===========================================================================
Step-by-Step Pipeline:
===========================================================================

    pipeline = OceanGraph(backend="gemini", api_key="key", input_dir="docs", output_dir="out")

    # Run individual steps
    chunks = pipeline.convert_and_chunk()       # PDF -> Markdown -> Chunks
    pipeline.embed(chunks)                      # Build FAISS index
    results = pipeline.generate(chunks)         # Generate QA pairs
    results = pipeline.deduplicate(results)     # Remove duplicates
    results.save("dataset.json")

===========================================================================
Configuration:
===========================================================================

    from oceangraph import OceanGraph, OceanGraphConfig

    # Full control
    config = OceanGraphConfig(
        backend="gemini",
        api_key="key",
        num_qa_pairs=200,
        embedding_model="nomic",
        ocr_engine="easyocr",
        device="cuda:0",
    )
    pipeline = OceanGraph(config=config)
    results = pipeline.run()

    # From YAML
    pipeline = OceanGraph.from_config("config.yaml", num_qa_pairs=50)

===========================================================================
Results:
===========================================================================

    results = pipeline.run()

    for qa in results:                    # Iterate
        print(qa['question'])

    results.save("dataset.json")          # Save as JSON
    results.save("dataset.jsonl", format="jsonl")  # Save as JSONL
    df = results.to_dataframe()           # pandas DataFrame
    d  = results.to_dict()                # dict

    loaded = OceanGraphResults.load("dataset.json")  # Load from file
"""

import os
import json
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union

logger = logging.getLogger(__name__)


# Environment variables temporarily owned by one high-level API run.  They are
# restored afterwards so notebooks and test processes can safely run two
# differently configured OceanGraph instances in sequence.
_MANAGED_RUNTIME_ENV = (
    "OCEANGRAPH_BACKEND",
    "LLM_BACKEND",
    "OCEANGRAPH_MODEL",
    "OCEANGRAPH_EMBEDDING_MODEL",
    "OCEANGRAPH_RERANKER_MODEL",
    "OCEANGRAPH_INPUT_DIR",
    "OCEANGRAPH_OUTPUT_DIR",
    "OCEANGRAPH_NUM_QA_PAIRS",
    "OCEANGRAPH_MAX_WORKERS",
    "OCEANGRAPH_MAX_DEPTH",
    "OCEANGRAPH_STRICT_MULTIHOP",
    "OCEANGRAPH_MIN_SUPPORTING_CHUNKS",
    "OCEANGRAPH_OUTPUT_JSONL",
    "OCEANGRAPH_MODEL_SELECTION",
    "OCEANGRAPH_VERIFICATION_PROFILE",
    "OCEANGRAPH_MAX_ANSWER_WORDS",
    "OCEANGRAPH_MAX_ANSWER_CJK_CHARS",
    "OCEANGRAPH_MULTIHOP_VERIFICATION_MODE",
    "OCEANGRAPH_MAX_VERIFICATION_CHUNKS",
    "OCEANGRAPH_MAX_UNKNOWN_VERDICTS",
    "OCEANGRAPH_COUNTERFACTUAL_VERIFICATION",
    "OCEANGRAPH_SKIP_PDF_PROCESSING",
    "OCEANGRAPH_SKIP_CHUNKING",
    "OCEANGRAPH_RUN_DEDUPLICATION",
    "OCEANGRAPH_RUN_EVALUATION",
    "OCEANGRAPH_ENABLE_CHECKPOINTING",
    "OCEANGRAPH_CONFIG",
    "CUDA_VISIBLE_DEVICES",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
)


def _snapshot_runtime_environment() -> Dict[str, Optional[str]]:
    return {name: os.environ.get(name) for name in _MANAGED_RUNTIME_ENV}


def _restore_runtime_environment(snapshot: Dict[str, Optional[str]]) -> None:
    for name, value in snapshot.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


# =============================================================================
# Configuration
# =============================================================================
@dataclass
class OceanGraphConfig:
    """
    Complete configuration for the OceanGraph pipeline.
    
    All parameters have sensible defaults. At minimum, you need:
    - ``input_dir``: Path to documents (PDFs, HTML, etc.)
    - ``output_dir``: Where to save results
    - ``backend``: LLM backend ("gemini", "openai", "ollama")
    - ``api_key``: API key for the chosen backend
    
    Example::
    
        config = OceanGraphConfig(
            input_dir="data/docs",
            output_dir="output",
            backend="gemini",
            api_key="your-key",
            num_qa_pairs=50,
            embedding_model="nomic",
            device="cuda:0",
        )
    """
    # =========================================================================
    # Core / Required
    # =========================================================================
    input_dir: str = "data/documents"
    output_dir: str = "output/results"
    backend: str = "gemini"
    api_key: Optional[str] = None
    
    # =========================================================================
    # Model Selection
    # =========================================================================
    llm_model: Optional[str] = None
    """LLM model name. Auto-selected per backend if None.
    Gemini: gemini-2.0-flash, OpenAI: gpt-4o-mini, Ollama: llama3"""
    
    vlm_model: Optional[str] = None
    """Vision-Language model name. Auto-selected per backend if None.
    Gemini: gemini-2.0-flash, OpenAI: gpt-4o, Ollama: llava"""
    
    embedding_model: str = "auto"
    """Embedding model: "auto", "nomic", "bge_m3", "gemini", "qwen3_vl", "qwen2_vl" """
    
    reranker_model: str = "gemini_vlm"
    """Reranker model: "gemini_vlm", "monovlm", "text_embedding" """
    
    # =========================================================================
    # QA Generation
    # =========================================================================
    num_qa_pairs: int = 10
    """Target number of QA pairs to generate."""
    
    qa_type: str = "multihop"
    """QA type: "multihop", "multimodal", "text", "mix" """
    
    max_depth: int = 2
    """Maximum depth for multi-hop context retrieval (1-20). Higher = more hops but more API calls."""
    
    max_breadth: int = 5
    """Maximum breadth for search verification (1-10). Higher = wider search per hop."""
    
    chunks_per_search: int = 2
    """Number of chunks retrieved per search query."""
    
    chunk_addition_mode: str = "RELATED"
    """How to add chunks during context building: "RELATED" or "EXPLANATORY" """

    strict_multihop_verification: bool = True
    """Reject QA pairs that can be answered from any single context chunk."""

    min_supporting_chunks: int = 2
    """Minimum number of distinct chunks required for strict multi-hop QA."""

    output_jsonl: bool = True
    """Also write JSONL copies of generated QA outputs."""

    model_selection: bool = False
    """Enable model-based candidate selection before verification."""

    verification_profile: str = "cost_efficient"
    """``cost_efficient`` uses one DeepSeek call per locally valid candidate."""

    max_answer_words: int = 12
    """Maximum whitespace-token count for the canonical EM answer."""

    max_answer_cjk_chars: int = 16
    """Maximum CJK-character count for the canonical EM answer."""

    multihop_verification_mode: str = "balanced"
    """Multi-hop verifier mode: ``balanced`` or ``strict``."""

    max_verification_chunks: int = 4
    """Maximum chunks checked by the balanced verifier."""

    max_unknown_verdicts: int = 1
    """Allowed unparseable chunk verdicts in balanced mode."""

    counterfactual_verification: bool = False
    """Enable leave-one-out evidence checks in strict mode."""
    
    # =========================================================================
    # Document Processing (PDF/HTML -> Markdown)
    # =========================================================================
    ocr_engine: str = "easyocr"
    """OCR engine for scanned documents: "easyocr" (default).
    EasyOCR supports 80+ languages and works on CPU and GPU."""
    
    image_resolution_scale: float = 2.0
    """Scale factor for image resolution during PDF processing (1.0-4.0)."""
    
    do_ocr: bool = True
    """Enable OCR for scanned PDFs."""
    
    do_table_structure: bool = True
    """Enable table structure extraction."""
    
    do_code_enrichment: bool = True
    """Enable code block enrichment."""
    
    do_formula_enrichment: bool = True
    """Enable formula/equation enrichment."""
    
    # =========================================================================
    # Chunking
    # =========================================================================
    chunk_window_size: int = 20000
    """Window size in characters for semantic chunking (default: 20000 ~ 5000 tokens)."""
    
    chunk_overlap_size: int = 2000
    """Overlap between chunking windows in characters (default: 2000 ~ 500 tokens)."""
    
    # =========================================================================
    # Embeddings & Indexing
    # =========================================================================
    embed_batch_size: int = 16
    """Batch size for embedding generation."""
    
    cache_embeddings: bool = True
    """Cache embeddings to disk for reuse across runs."""
    
    faiss_use_gpu: bool = False
    """Use GPU for FAISS similarity search (requires faiss-gpu via conda)."""
    
    faiss_gpu_id: int = 0
    """GPU ID for FAISS (if faiss_use_gpu=True)."""
    
    # =========================================================================
    # Parallel Processing
    # =========================================================================
    max_workers: int = 4
    """Number of parallel workers for QA generation."""
    
    num_cpu_workers: int = 3
    """Number of CPU workers for document processing."""
    
    dedup_max_workers: int = 4
    """Number of workers for deduplication."""
    
    # =========================================================================
    # Rate Limiting
    # =========================================================================
    requests_per_minute: int = 60
    """API rate limit (requests per minute)."""
    
    burst_size: int = 15
    """Burst size for rate limiting."""
    
    # =========================================================================
    # Device & GPU
    # =========================================================================
    device: Optional[str] = None
    """Device for model inference: "cuda", "cuda:0", "cuda:1", "cpu", or None (auto-detect).
    When None, GPU is used if available, otherwise CPU."""
    
    embedding_gpus: Optional[List[int]] = None
    """List of GPU IDs for embedding model (e.g., [0], [0,1]). None = auto."""
    
    pdf_processing_gpus: Optional[List[int]] = None
    """List of GPU IDs for PDF processing workers. None = auto."""
    
    # =========================================================================
    # Pipeline Control
    # =========================================================================
    skip_pdf_processing: bool = False
    """Skip PDF-to-Markdown conversion (use existing markdown files)."""
    
    skip_chunking: bool = False
    """Skip semantic chunking (use existing chunks.json)."""
    
    run_deduplication: bool = False
    """Enable QA pair deduplication after generation."""
    
    run_evaluation: bool = False
    """Enable evaluation metrics computation (requires [eval] extras)."""
    
    enable_checkpointing: bool = True
    """Enable checkpoint/resume for long-running pipelines."""

    export_training_data: bool = True
    """Write compact verified QA and corpus JSONL files for downstream training."""

    training_split: str = "train"
    """Split label stored in the automatic training export."""
    
    max_pages: Optional[int] = None
    """Maximum number of pages to process. None = no limit."""
    
    max_pdfs: Optional[int] = None
    """Maximum number of PDF files to process. None = no limit."""
    
    sort_by_size: bool = True
    """Sort documents by file size (smallest first) for processing."""

    max_chunks: Optional[int] = None
    """Maximum chunks used for QA generation. None processes all chunks."""

    shuffle: bool = True
    """Shuffle seed chunks before generation."""

    shuffle_seed: int = 42
    """Deterministic seed used when shuffling chunks."""

    text_only_mode: bool = True
    """Exclude visual inputs and metadata from model calls and exports."""
    
    # =========================================================================
    # QA Correction
    # =========================================================================
    qa_correction_enabled: bool = False
    """Enable automatic QA correction pass."""
    
    qa_correction_max_attempts: int = 0
    """Maximum correction attempts per QA pair."""
    
    # =========================================================================
    # Deduplication
    # =========================================================================
    dedup_alpha: float = 0.6
    """Alpha parameter for deduplication scoring."""
    
    dedup_question_similarity_threshold: float = 0.75
    """Similarity threshold for question deduplication."""
    
    # =========================================================================
    # Advanced
    # =========================================================================
    config_file: Optional[str] = None
    """Path to config.yaml for full YAML-based configuration. 
    When provided, YAML values are used as base, and other parameters override them."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {k: v for k, v in self.__dict__.items()}

    def to_runtime_config(self) -> Dict[str, Any]:
        """Build the complete nested configuration consumed by one run.

        If this object originated from YAML, model routing profiles and other
        extension keys are retained while explicitly configured public fields
        override their file-backed values.
        """
        base: Dict[str, Any] = {}
        if self.config_file and Path(self.config_file).is_file():
            from oceangraph.core.config import load_config

            loaded = load_config(self.config_file)
            if isinstance(loaded, dict):
                base = loaded

        overlay = {
            "backend": {
                "active": self.backend.upper(),
                self.backend.lower(): {
                    key: value
                    for key, value in {
                        "llm_model": self.llm_model,
                        "vlm_model": self.vlm_model,
                    }.items()
                    if value is not None
                },
            },
            "pipeline": {"modality": "text" if self.text_only_mode else "multimodal"},
            "paths": {
                "input_pdf_dir": self.input_dir,
                "output_dir": self.output_dir,
            },
            "processing": {
                "max_pdfs": self.max_pdfs,
                "sort_by_size": self.sort_by_size,
                "max_chunks": self.max_chunks,
            },
            "chunking": {
                "window_size": self.chunk_window_size,
                "overlap_size": self.chunk_overlap_size,
            },
            "shuffling": {"enabled": self.shuffle, "seed": self.shuffle_seed},
            "qa_generation": {
                "num_qa_pairs": self.num_qa_pairs,
                "type": self.qa_type,
                "strict_multihop_verification": self.strict_multihop_verification,
                "min_supporting_chunks": self.min_supporting_chunks,
                "output_jsonl": self.output_jsonl,
                "model_selection": self.model_selection,
                "verification_profile": self.verification_profile,
                "max_answer_words": self.max_answer_words,
                "max_answer_cjk_chars": self.max_answer_cjk_chars,
                "multihop_verification_mode": self.multihop_verification_mode,
                "max_verification_chunks": self.max_verification_chunks,
                "max_unknown_verdicts": self.max_unknown_verdicts,
                "counterfactual_verification": self.counterfactual_verification,
            },
            "retrieval": {
                "multihop": {
                    "max_depth": self.max_depth,
                    "max_breadth": self.max_breadth,
                    "chunks_per_search": self.chunks_per_search,
                    "chunk_addition_mode": self.chunk_addition_mode,
                }
            },
            "embedding": {
                "model": self.embedding_model,
                "batch_size": self.embed_batch_size,
                "cache_embeddings": self.cache_embeddings,
                "gpus": self.embedding_gpus,
            },
            "parallel": {
                "num_workers": self.num_cpu_workers,
                "qa_max_workers": self.max_workers,
                "dedup_max_workers": self.dedup_max_workers,
            },
            "rate_limiting": {
                "requests_per_minute": self.requests_per_minute,
                "burst_size": self.burst_size,
            },
            "faiss": {"use_gpu": self.faiss_use_gpu, "gpu_id": self.faiss_gpu_id},
            "deduplication": {
                "enabled": self.run_deduplication,
                "alpha": self.dedup_alpha,
                "question_similarity_threshold": self.dedup_question_similarity_threshold,
                "preserve_verified_records": True,
            },
            "qa_correction": {
                "enabled": self.qa_correction_enabled,
                "max_attempts": self.qa_correction_max_attempts,
            },
            "evaluation": {"run_evaluation": self.run_evaluation},
            "checkpointing": {"enabled": self.enable_checkpointing},
            "training_export": {
                "enabled": self.export_training_data,
                "split": self.training_split,
            },
            "pdf_processing": {
                "ocr_engine": self.ocr_engine,
                "image_resolution_scale": self.image_resolution_scale,
                "do_ocr": self.do_ocr,
                "do_table_structure": self.do_table_structure,
                "do_code_enrichment": self.do_code_enrichment,
                "do_formula_enrichment": self.do_formula_enrichment,
            },
        }

        def merge(target: Dict[str, Any], updates: Dict[str, Any]) -> None:
            for key, value in updates.items():
                if isinstance(value, dict) and isinstance(target.get(key), dict):
                    merge(target[key], value)
                else:
                    target[key] = value

        merge(base, overlay)
        return base
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "OceanGraphConfig":
        """Create configuration from a dictionary.
        
        Unknown keys are silently ignored, making it safe to pass
        partial or extra configurations.
        """
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in d.items() if k in valid_fields}
        return cls(**filtered)
    
    @classmethod
    def from_yaml(cls, path: str) -> "OceanGraphConfig":
        """
        Load configuration from a YAML file (config.yaml format).
        
        Maps the nested YAML structure to flat OceanGraphConfig fields.
        
        Args:
            path: Path to config.yaml
        
        Returns:
            OceanGraphConfig instance.
        """
        from oceangraph.core.config import load_config

        data = load_config(path)
        
        # Map YAML structure to flat config
        backend_cfg = data.get('backend', {})
        active = backend_cfg.get('active', 'GEMINI').lower()
        active_cfg = backend_cfg.get(active, {})
        paths = data.get('paths', {})
        processing = data.get('processing', {})
        parallel = data.get('parallel', {})
        embedding = data.get('embedding', {})
        retrieval = data.get('retrieval', {}).get('multihop', {})
        qa_gen = data.get('qa_generation', {})
        rate_limit = data.get('rate_limiting', {})
        pdf = data.get('pdf_processing', {})
        dedup = data.get('deduplication', {})
        qa_corr = data.get('qa_correction', {})
        chunking = data.get('chunking', {})
        faiss_cfg = data.get('faiss', {})
        eval_cfg = data.get('evaluation', {})
        
        return cls(
            # Core
            input_dir=paths.get('input_pdf_dir', 'data/documents'),
            output_dir=paths.get('output_dir', 'output/results'),
            backend=active,
            llm_model=active_cfg.get('llm_model'),
            vlm_model=active_cfg.get('vlm_model'),
            # Models
            embedding_model=embedding.get('model', 'auto'),
            # QA Generation
            num_qa_pairs=qa_gen.get('num_qa_pairs', 10),
            qa_type=qa_gen.get('type', 'multihop'),
            max_depth=retrieval.get('max_depth', 2),
            max_breadth=retrieval.get('max_breadth', 5),
            chunks_per_search=retrieval.get('chunks_per_search', 2),
            chunk_addition_mode=retrieval.get('chunk_addition_mode', 'RELATED'),
            strict_multihop_verification=qa_gen.get('strict_multihop_verification', True),
            min_supporting_chunks=qa_gen.get('min_supporting_chunks', 2),
            output_jsonl=qa_gen.get('output_jsonl', True),
            model_selection=qa_gen.get('model_selection', False),
            verification_profile=qa_gen.get(
                'verification_profile', 'cost_efficient'
            ),
            max_answer_words=qa_gen.get('max_answer_words', 12),
            max_answer_cjk_chars=qa_gen.get('max_answer_cjk_chars', 16),
            multihop_verification_mode=qa_gen.get(
                'multihop_verification_mode', 'balanced'
            ),
            max_verification_chunks=qa_gen.get('max_verification_chunks', 4),
            max_unknown_verdicts=qa_gen.get('max_unknown_verdicts', 1),
            counterfactual_verification=qa_gen.get(
                'counterfactual_verification', False
            ),
            # Processing
            max_workers=parallel.get('qa_max_workers', 4),
            num_cpu_workers=parallel.get('num_workers', 3),
            dedup_max_workers=parallel.get('dedup_max_workers', 4),
            embed_batch_size=embedding.get('batch_size', 16),
            embedding_gpus=embedding.get('gpus'),
            max_pdfs=processing.get('max_pdfs'),
            sort_by_size=processing.get('sort_by_size', True),
            max_chunks=processing.get('max_chunks'),
            chunk_window_size=chunking.get('window_size', 20000),
            chunk_overlap_size=chunking.get('overlap_size', 2000),
            shuffle=(data.get('shuffling') or {}).get('enabled', True),
            shuffle_seed=(data.get('shuffling') or {}).get('seed', 42),
            text_only_mode=str((data.get('pipeline') or {}).get('modality', 'text')).lower()
            == 'text',
            # PDF processing
            image_resolution_scale=pdf.get('image_resolution_scale', 2.0),
            # Rate limiting
            requests_per_minute=rate_limit.get('requests_per_minute', 60),
            burst_size=rate_limit.get('burst_size', 15),
            # FAISS
            faiss_use_gpu=faiss_cfg.get('use_gpu', False),
            faiss_gpu_id=faiss_cfg.get('gpu_id', 0),
            # Dedup
            dedup_alpha=dedup.get('alpha', 0.6),
            dedup_question_similarity_threshold=dedup.get('question_similarity_threshold', 0.75),
            run_deduplication=dedup.get('enabled', False),
            # QA correction
            qa_correction_enabled=qa_corr.get('enabled', False),
            qa_correction_max_attempts=qa_corr.get('max_attempts', 0),
            # Eval
            run_evaluation=eval_cfg.get('run_evaluation', False),
            enable_checkpointing=(data.get('checkpointing') or {}).get('enabled', True),
            export_training_data=(data.get('training_export') or {}).get('enabled', True),
            training_split=(data.get('training_export') or {}).get('split', 'train'),
            # File reference
            config_file=path,
        )
    
    def save_yaml(self, path: str):
        """
        Save configuration to a YAML file.
        
        Args:
            path: Output YAML file path.
        """
        import yaml
        
        data = self.to_runtime_config()
        if data.get("llm_config_file"):
            for section in ("backend", "models", "rate_limiting"):
                data.pop(section, None)
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


# =============================================================================
# Results
# =============================================================================
@dataclass
class OceanGraphResults:
    """
    Container for OceanGraph pipeline results.
    
    Supports iteration, indexing, save/load, and DataFrame conversion.
    
    Example::
    
        results = pipeline.run()
        
        # Iterate
        for qa in results:
            print(qa['question'])
        
        # Index
        first = results[0]
        
        # Length
        print(f"Generated {len(results)} QA pairs")
        
        # Save/Load
        results.save("dataset.json")
        loaded = OceanGraphResults.load("dataset.json")
        
        # pandas
        df = results.to_dataframe()
    """
    qa_pairs: List[Dict[str, Any]] = field(default_factory=list)
    chunks: List[Dict[str, Any]] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)
    output_dir: Optional[str] = None
    config: Optional[OceanGraphConfig] = None
    
    def __len__(self) -> int:
        return len(self.qa_pairs)
    
    def __iter__(self):
        return iter(self.qa_pairs)
    
    def __getitem__(self, idx):
        return self.qa_pairs[idx]
    
    def __bool__(self) -> bool:
        return len(self.qa_pairs) > 0
    
    def __repr__(self) -> str:
        return (
            f"OceanGraphResults(qa_pairs={len(self.qa_pairs)}, "
            f"chunks={len(self.chunks)}, "
            f"output_dir='{self.output_dir}')"
        )
    
    @property
    def questions(self) -> List[str]:
        """List of all questions."""
        return [qa.get('question', '') for qa in self.qa_pairs]
    
    @property
    def answers(self) -> List[str]:
        """List of all answers."""
        return [qa.get('answer', '') for qa in self.qa_pairs]
    
    def save(self, path: Optional[str] = None, format: str = "json") -> str:
        """
        Save QA pairs to a file.
        
        Args:
            path: Output path. If None, saves to ``output_dir/qa_pairs.json``.
            format: ``"json"`` (default) or ``"jsonl"`` (one JSON object per line).
        
        Returns:
            Path to the saved file.
        """
        if path is None:
            path = os.path.join(self.output_dir or ".", "qa_pairs.json")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        if format == "jsonl":
            with open(path, 'w') as f:
                for qa in self.qa_pairs:
                    f.write(json.dumps(qa) + '\n')
        else:
            with open(path, 'w') as f:
                json.dump(self.qa_pairs, f, indent=2)
        
        logger.info(f"Saved {len(self.qa_pairs)} QA pairs to {path}")
        return path
    
    def to_dataframe(self):
        """
        Convert QA pairs to a pandas DataFrame.
        
        Returns:
            pandas.DataFrame with columns for question, answer, type, difficulty, etc.
        """
        import pandas as pd
        if not self.qa_pairs:
            return pd.DataFrame()
        
        rows = []
        for qa in self.qa_pairs:
            row = {
                'question': qa.get('question', ''),
                'answer': qa.get('answer', ''),
                'question_type': qa.get('question_type', ''),
                'subdomain': qa.get('subdomain', ''),
                'difficulty': qa.get('difficulty_score', qa.get('difficulty', '')),
                'num_hops': qa.get('hop_count', qa.get('declared_hop_count', 0)),
                'strict_multihop_status': qa.get('multihop_necessity_result', {}).get('status', ''),
            }
            for k, v in qa.items():
                if k not in row and isinstance(v, (str, int, float, bool)):
                    row[k] = v
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert results to a dictionary."""
        return {
            'qa_pairs': self.qa_pairs,
            'stats': self.stats,
            'num_qa_pairs': len(self.qa_pairs),
            'num_chunks': len(self.chunks),
        }

    def export_training(
        self,
        path: Optional[str] = None,
        *,
        split: str = "train",
    ) -> Dict[str, Any]:
        """Export only fully verified multi-agent records for model training."""
        from oceangraph.training import export_training_dataset

        output_path = path or os.path.join(self.output_dir or ".", "training")
        return export_training_dataset(
            self.qa_pairs,
            self.chunks,
            output_path,
            split=split,
        )
    
    def filter(self, **kwargs) -> "OceanGraphResults":
        """
        Filter QA pairs by field values.
        
        Example::
        
            multihop = results.filter(question_type="multihop")
            hard = results.filter(difficulty="hard")
        
        Returns:
            New OceanGraphResults with filtered QA pairs.
        """
        filtered = []
        for qa in self.qa_pairs:
            if all(qa.get(k) == v for k, v in kwargs.items()):
                filtered.append(qa)
        return OceanGraphResults(
            qa_pairs=filtered,
            chunks=self.chunks,
            stats=self.stats,
            output_dir=self.output_dir,
            config=self.config,
        )
    
    def sample(self, n: int, seed: int = 42) -> "OceanGraphResults":
        """
        Random sample of QA pairs.
        
        Args:
            n: Number of QA pairs to sample.
            seed: Random seed for reproducibility.
        
        Returns:
            New OceanGraphResults with sampled QA pairs.
        """
        import random
        rng = random.Random(seed)
        sampled = rng.sample(self.qa_pairs, min(n, len(self.qa_pairs)))
        return OceanGraphResults(
            qa_pairs=sampled,
            chunks=self.chunks,
            stats=self.stats,
            output_dir=self.output_dir,
            config=self.config,
        )
    
    @classmethod
    def load(cls, path: str) -> "OceanGraphResults":
        """
        Load QA pairs from a JSON or JSONL file.
        
        Args:
            path: Path to JSON or JSONL file.
        
        Returns:
            OceanGraphResults instance.
        """
        path = str(path)
        
        if path.endswith('.jsonl'):
            qa_pairs = []
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        qa_pairs.append(json.loads(line))
            return cls(qa_pairs=qa_pairs)
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return cls(qa_pairs=data)
        elif isinstance(data, dict) and 'qa_pairs' in data:
            return cls(qa_pairs=data['qa_pairs'], stats=data.get('stats', {}))
        else:
            return cls(qa_pairs=[data] if isinstance(data, dict) else data)


# =============================================================================
# Main Pipeline Class
# =============================================================================
class OceanGraph:
    """
    OceanGraph: Multimodal Multihop RAG Evaluation Dataset Generator.
    
    A complete pipeline for generating QA datasets from documents.
    
    =========================================================================
    Quick Start:
    =========================================================================
    
    ::
    
        from oceangraph import OceanGraph
        
        pipeline = OceanGraph(
            input_dir="data/my_docs",
            output_dir="output/results",
            backend="gemini",
            api_key="your-gemini-api-key",
        )
        results = pipeline.run()
        results.save("my_dataset.json")
    
    =========================================================================
    From Config:
    =========================================================================
    
    ::
    
        pipeline = OceanGraph.from_config("config.yaml")
        pipeline.configure(num_qa_pairs=100)
        results = pipeline.run()
    
    =========================================================================
    Advanced:
    =========================================================================
    
    ::
    
        pipeline = OceanGraph(
            input_dir="data/papers",
            output_dir="output/papers_qa",
            backend="gemini",
            api_key="your-key",
            num_qa_pairs=200,
            max_depth=3,
            embedding_model="nomic",
            reranker_model="gemini_vlm",
            ocr_engine="easyocr",
            device="cuda:0",
            embedding_gpus=[0],
            run_deduplication=True,
        )
        results = pipeline.run()
        df = results.to_dataframe()
    """
    
    def __init__(self, config: Optional[OceanGraphConfig] = None, **kwargs):
        """
        Initialize OceanGraph pipeline.
        
        Can be initialized with a OceanGraphConfig object OR keyword arguments.
        
        Args:
            config: OceanGraphConfig instance (takes precedence over kwargs).
            **kwargs: Configuration parameters (see OceanGraphConfig for all options).
        
        Example::
        
            # With keyword arguments
            pipeline = OceanGraph(
                input_dir="docs",
                backend="gemini",
                api_key="key",
                num_qa_pairs=50,
            )
            
            # With config object
            config = OceanGraphConfig(backend="gemini", api_key="key")
            pipeline = OceanGraph(config=config)
        """
        if config is not None:
            self.config = config
        else:
            self.config = OceanGraphConfig(**kwargs)
        self._is_configured = False
    
    @classmethod
    def from_config(cls, config_path: str, **overrides) -> "OceanGraph":
        """
        Create pipeline from a YAML configuration file.
        
        Args:
            config_path: Path to config.yaml
            **overrides: Override any config values (e.g., num_qa_pairs=50)
        
        Returns:
            Configured OceanGraph pipeline.
        
        Example::
        
            pipeline = OceanGraph.from_config("config.yaml", num_qa_pairs=50, api_key="key")
        """
        config = OceanGraphConfig.from_yaml(config_path)
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        instance = cls.__new__(cls)
        instance.config = config
        instance._is_configured = False
        return instance
    
    def configure(self, **kwargs) -> "OceanGraph":
        """
        Update pipeline configuration. Returns self for method chaining.
        
        Args:
            **kwargs: Any OceanGraphConfig parameter to update.
        
        Returns:
            self (for chaining)
        
        Raises:
            ValueError: If an unknown parameter is passed.
        
        Example::
        
            results = pipeline.configure(num_qa_pairs=100, max_depth=3).run()
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                valid = list(self.config.__dataclass_fields__.keys())
                raise ValueError(
                    f"Unknown parameter: '{key}'. Valid parameters: {valid}"
                )
        self._is_configured = False
        return self
    
    def _setup_environment(self):
        """Apply OceanGraphConfig to environment variables before pipeline import."""
        cfg = self.config
        
        # Setup device
        from oceangraph.utils.device import setup_device_environment
        setup_device_environment()
        
        # Backend and API key
        os.environ["OCEANGRAPH_BACKEND"] = cfg.backend.upper()
        os.environ["LLM_BACKEND"] = cfg.backend.upper()
        if cfg.api_key:
            if cfg.backend.lower() == "gemini":
                os.environ["GEMINI_API_KEY"] = cfg.api_key
                os.environ["GOOGLE_API_KEY"] = cfg.api_key
            elif cfg.backend.lower() == "openai":
                os.environ["OPENAI_API_KEY"] = cfg.api_key
        
        # Models
        if cfg.llm_model:
            os.environ["OCEANGRAPH_MODEL"] = cfg.llm_model
        else:
            os.environ.pop("OCEANGRAPH_MODEL", None)
        if cfg.embedding_model and cfg.embedding_model != "auto":
            os.environ["OCEANGRAPH_EMBEDDING_MODEL"] = cfg.embedding_model
        else:
            os.environ.pop("OCEANGRAPH_EMBEDDING_MODEL", None)
        if cfg.reranker_model:
            os.environ["OCEANGRAPH_RERANKER_MODEL"] = cfg.reranker_model
        else:
            os.environ.pop("OCEANGRAPH_RERANKER_MODEL", None)
        
        # Paths
        os.environ["OCEANGRAPH_INPUT_DIR"] = str(cfg.input_dir)
        os.environ["OCEANGRAPH_OUTPUT_DIR"] = str(cfg.output_dir)
        
        # QA generation
        os.environ["OCEANGRAPH_NUM_QA_PAIRS"] = str(cfg.num_qa_pairs)
        os.environ["OCEANGRAPH_MAX_WORKERS"] = str(cfg.max_workers)
        os.environ["OCEANGRAPH_MAX_DEPTH"] = str(cfg.max_depth)
        os.environ["OCEANGRAPH_STRICT_MULTIHOP"] = "1" if cfg.strict_multihop_verification else "0"
        os.environ["OCEANGRAPH_MIN_SUPPORTING_CHUNKS"] = str(cfg.min_supporting_chunks)
        os.environ["OCEANGRAPH_OUTPUT_JSONL"] = "1" if cfg.output_jsonl else "0"
        os.environ["OCEANGRAPH_MODEL_SELECTION"] = "1" if cfg.model_selection else "0"
        os.environ["OCEANGRAPH_VERIFICATION_PROFILE"] = cfg.verification_profile
        os.environ["OCEANGRAPH_MAX_ANSWER_WORDS"] = str(cfg.max_answer_words)
        os.environ["OCEANGRAPH_MAX_ANSWER_CJK_CHARS"] = str(
            cfg.max_answer_cjk_chars
        )
        os.environ["OCEANGRAPH_MULTIHOP_VERIFICATION_MODE"] = cfg.multihop_verification_mode
        os.environ["OCEANGRAPH_MAX_VERIFICATION_CHUNKS"] = str(cfg.max_verification_chunks)
        os.environ["OCEANGRAPH_MAX_UNKNOWN_VERDICTS"] = str(cfg.max_unknown_verdicts)
        os.environ["OCEANGRAPH_COUNTERFACTUAL_VERIFICATION"] = (
            "1" if cfg.counterfactual_verification else "0"
        )
        
        # Pipeline flags
        os.environ["OCEANGRAPH_SKIP_PDF_PROCESSING"] = "1" if cfg.skip_pdf_processing else "0"
        os.environ["OCEANGRAPH_SKIP_CHUNKING"] = "1" if cfg.skip_chunking else "0"
        os.environ["OCEANGRAPH_RUN_DEDUPLICATION"] = "1" if cfg.run_deduplication else "0"
        os.environ["OCEANGRAPH_RUN_EVALUATION"] = "1" if cfg.run_evaluation else "0"
        os.environ["OCEANGRAPH_ENABLE_CHECKPOINTING"] = (
            "1" if cfg.enable_checkpointing else "0"
        )
        
        # Device
        if cfg.device == "cpu":
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        
        # Config file
        if cfg.config_file and os.path.exists(cfg.config_file):
            os.environ["OCEANGRAPH_CONFIG"] = cfg.config_file
        else:
            os.environ.pop("OCEANGRAPH_CONFIG", None)

        from oceangraph.core.config import set_runtime_config
        from oceangraph.core.llm import reset_llm_runtime

        set_runtime_config(cfg.to_runtime_config())
        reset_llm_runtime(reset_tokens=True)
        
        self._is_configured = True
    
    def _get_project_root(self) -> Path:
        """Find project root (where config.yaml lives), or use cwd."""
        # Check common locations
        for candidate in [
            Path(__file__).parent.parent.parent,  # src/oceangraph/api.py -> project root
            Path.cwd(),
        ]:
            if (candidate / "config.yaml").exists():
                return candidate
        return Path.cwd()
    
    def preflight(self) -> bool:
        """
        Run preflight checks to validate the pipeline configuration.
        
        Tests all services: config, API key, LLM, VLM, embeddings, reranker.
        
        Returns:
            True if all checks passed.
        
        Example::
        
            if pipeline.preflight():
                results = pipeline.run()
            else:
                print("Fix configuration issues first")
        """
        environment_snapshot = _snapshot_runtime_environment()
        original_cwd = os.getcwd()
        try:
            self._setup_environment()
            project_root = self._get_project_root()
            os.chdir(project_root)
            from oceangraph.utils.preflight import run_preflight_checks
            all_passed, _ = run_preflight_checks()
            return all_passed
        finally:
            os.chdir(original_cwd)
            from oceangraph.core.config import clear_runtime_config
            from oceangraph.core.llm import reset_llm_runtime

            clear_runtime_config()
            reset_llm_runtime(reset_tokens=True)
            _restore_runtime_environment(environment_snapshot)
    
    def run(self) -> OceanGraphResults:
        """
        Run the complete OceanGraph pipeline.
        
        Executes all steps:
            1. Corpus Agent: parsing, chunking, taxonomy, and indexing
            2. Evidence Agent: evidence retrieval and context completion
            3. QA Agent: QA synthesis and reasoning annotation
            4. Verifier Agent: atomicity, grounding, and multi-hop necessity
            5. (Optional) Deduplication
            6. (Optional) Evaluation
        
        Returns:
            OceanGraphResults with generated QA pairs, chunks, and statistics.
        
        Example::
        
            results = pipeline.run()
            print(f"Generated {len(results)} QA pairs")
            results.save("dataset.json")
        """
        cfg = self.config
        Path(cfg.output_dir).mkdir(parents=True, exist_ok=True)
        environment_snapshot = _snapshot_runtime_environment()
        original_cwd = os.getcwd()
        try:
            # Always configure: ``configure()`` is not the only way external
            # code may mutate the dataclass between repeated runs.
            self._setup_environment()
            project_root = self._get_project_root()
            os.chdir(project_root)
            from oceangraph.engine import run_pipeline
            run_pipeline(cfg)
            return self._collect_results()
        finally:
            os.chdir(original_cwd)
            from oceangraph.core.config import clear_runtime_config
            from oceangraph.core.llm import reset_llm_runtime

            clear_runtime_config()
            reset_llm_runtime(reset_tokens=True)
            _restore_runtime_environment(environment_snapshot)
            self._is_configured = False
    
    def _collect_results(self) -> OceanGraphResults:
        """Collect results from the output directory after pipeline execution."""
        cfg = self.config
        out = Path(cfg.output_dir)
        
        # Load QA pairs
        qa_pairs = []
        qa_candidates = (
            ["qa_deduplicated.json", "qa_multihop_pass.json"]
            if cfg.run_deduplication
            else ["qa_multihop_pass.json"]
        )
        for qa_file in qa_candidates:
            p = out / qa_file
            if p.exists():
                with open(p, 'r') as f:
                    qa_pairs = json.load(f)
                break
        
        # Load chunks
        chunks = []
        chunks_file = out / "chunks.json"
        if chunks_file.exists():
            with open(chunks_file, 'r') as f:
                chunks = json.load(f)
        
        # Gather statistics
        token_stats = {}
        try:
            from oceangraph.core.llm import get_token_stats
            token_stats = get_token_stats()
        except Exception:
            pass
        
        stats = {
            "total_qa_pairs": len(qa_pairs),
            "total_chunks": len(chunks),
            "backend": cfg.backend,
            "num_qa_pairs_requested": cfg.num_qa_pairs,
            **token_stats,
        }
        from oceangraph.agents import (
            AGENT_ARCHITECTURE_VERSION,
            get_agent_manifest,
        )

        stats["agent_architecture"] = {
            "version": AGENT_ARCHITECTURE_VERSION,
            "agents": get_agent_manifest(),
        }
        
        return OceanGraphResults(
            qa_pairs=qa_pairs,
            chunks=chunks,
            stats=stats,
            output_dir=cfg.output_dir,
            config=cfg,
        )
    
    def get_config(self) -> OceanGraphConfig:
        """Return the current pipeline configuration."""
        return self.config
    
    def save_config(self, path: str):
        """
        Save the current configuration to a YAML file.
        
        Args:
            path: Output YAML file path.
        
        Example::
        
            pipeline.save_config("my_config.yaml")
        """
        self.config.save_yaml(path)
    
    def __repr__(self) -> str:
        c = self.config
        parts = [f"backend='{c.backend}'", f"input_dir='{c.input_dir}'"]
        if c.num_qa_pairs:
            parts.append(f"num_qa_pairs={c.num_qa_pairs}")
        if c.device:
            parts.append(f"device='{c.device}'")
        if c.embedding_model != "auto":
            parts.append(f"embedding_model='{c.embedding_model}'")
        return f"OceanGraph({', '.join(parts)})"
