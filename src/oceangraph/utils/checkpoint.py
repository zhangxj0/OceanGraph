#!/usr/bin/env python3
"""
Checkpoint Management for OceanGraph Pipeline

Provides checkpointing at multiple stages:
1. Markdown conversion (per file)
2. Chunking (per file, then final)
3. Context building (per chunk)
4. QA generation (per chunk)

Enables resume from any checkpoint after interruption.
"""

import json
import os
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from datetime import datetime
import logging


RUN_MANIFEST_NAME = "oceangraph_run_manifest.json"
MATERIAL_OUTPUTS = {
    "chunks.json",
    "qa_multihop_pass.json",
    "qa_multihop_fail.json",
    "qa_deduplicated.json",
}


def _semantic_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Remove execution-only settings from a resumable dataset identity.

    The fingerprint protects data semantics, not the mechanics used to finish a
    run.  Targets, worker counts, paths, logging, preflight, evaluation, and
    export controls may change between a small smoke run and a resumed formal
    run without invalidating already verified records.
    """
    cleaned = dict(_safe_config(config or {}))
    for section in (
        "paths",
        "parallel",
        "preflight",
        "logging",
        "evaluation",
        "training_export",
        "deduplication",
    ):
        cleaned.pop(section, None)
    cleaned.pop("llm_config_file", None)

    qa_generation = dict(cleaned.get("qa_generation") or {})
    qa_generation.pop("num_qa_pairs", None)
    qa_generation.pop("output_jsonl", None)
    if qa_generation:
        cleaned["qa_generation"] = qa_generation
    else:
        cleaned.pop("qa_generation", None)

    embedding = dict(cleaned.get("embedding") or {})
    for key in ("batch_size", "gpus", "cache_embeddings", "local_files_only"):
        embedding.pop(key, None)
    if embedding:
        cleaned["embedding"] = embedding
    else:
        cleaned.pop("embedding", None)

    pdf_processing = dict(cleaned.get("pdf_processing") or {})
    for key in ("input_path", "output_dir", "num_threads", "cuda_device_id"):
        pdf_processing.pop(key, None)
    if pdf_processing:
        cleaned["pdf_processing"] = pdf_processing
    else:
        cleaned.pop("pdf_processing", None)

    domain_expert = dict(cleaned.get("domain_expert") or {})
    domain_expert.pop("output_dir", None)
    if domain_expert:
        cleaned["domain_expert"] = domain_expert
    else:
        cleaned.pop("domain_expert", None)
    return cleaned


def _semantic_runtime_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Return resolved settings that can change generated record semantics."""
    cleaned = dict(_safe_config(settings or {}))
    for section in ("paths", "parallel", "outputs"):
        cleaned.pop(section, None)

    qa_generation = dict(cleaned.get("qa_generation") or {})
    qa_generation.pop("target", None)
    if qa_generation:
        cleaned["qa_generation"] = qa_generation
    else:
        cleaned.pop("qa_generation", None)

    embedding = dict(cleaned.get("embedding") or {})
    for key in ("batch_size", "gpus", "cache"):
        embedding.pop(key, None)
    if embedding:
        cleaned["embedding"] = embedding
    else:
        cleaned.pop("embedding", None)

    faiss = dict(cleaned.get("faiss") or {})
    faiss.pop("use_gpu", None)
    faiss.pop("gpu_id", None)
    if faiss:
        cleaned["faiss"] = faiss
    else:
        cleaned.pop("faiss", None)
    return cleaned


def _safe_config(value: Any, key: str = "") -> Any:
    """Return a deterministic config copy with any credential fields redacted."""
    if isinstance(value, dict):
        return {str(k): _safe_config(v, str(k)) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [_safe_config(item, key) for item in value]
    lowered = key.casefold()
    if any(token in lowered for token in ("api_key", "token", "password", "secret")):
        return "<redacted>"
    return value


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_run_fingerprint(
    config: Dict[str, Any],
    input_dir: str | None,
    input_chunks_file: str | None = None,
    *,
    framework_version: str = "3.0.0",
    runtime_settings: Dict[str, Any] | None = None,
    model_routes: Dict[str, Any] | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """Hash source config, effective runtime settings, routes, and corpus."""
    source_files: List[Path] = []
    if input_chunks_file and Path(input_chunks_file).is_file():
        source_files = [Path(input_chunks_file).resolve()]
        source_root = source_files[0].parent
    elif input_dir and Path(input_dir).is_dir():
        source_root = Path(input_dir).resolve()
        from oceangraph.utils.sources import discover_source_documents

        source_files = [
            path.resolve()
            for path in discover_source_documents(
                source_root,
                require_unique_stems=True,
            )
        ]
    else:
        source_root = Path(input_dir or ".").resolve()

    sources = []
    for path in source_files:
        try:
            relative = path.relative_to(source_root).as_posix()
        except ValueError:
            relative = path.name
        sources.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": _sha256_file(path),
            }
        )

    payload = {
        "framework_version": framework_version,
        "config": _semantic_config(config),
        "runtime_settings": _semantic_runtime_settings(runtime_settings or {}),
        "model_routes": _safe_config(model_routes or {}),
        "sources": sources,
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest(), payload


def validate_output_fingerprint(
    output_dir: str,
    fingerprint: str,
    metadata: Dict[str, Any],
    *,
    write_manifest: bool = True,
) -> Path:
    """Refuse to mix artifacts produced from a different config or corpus.

    A stale manifest may be replaced only while no material dataset artifacts
    exist.  ``write_manifest=False`` performs the paid-call safety check without
    claiming an output directory before mandatory preflight succeeds.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path / RUN_MANIFEST_NAME
    existing = None
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Cannot read existing run manifest: {manifest_path}") from exc

    has_material_outputs = any((output_path / name).exists() for name in MATERIAL_OUTPUTS)
    if existing and existing.get("fingerprint") != fingerprint and has_material_outputs:
        raise RuntimeError(
            "Output directory belongs to a different OceanGraph corpus/configuration. "
            f"Use a new output directory instead of mixing artifacts: {output_path}"
        )
    if existing is None and has_material_outputs:
        raise RuntimeError(
            "Existing OceanGraph artifacts have no v3.0.0 fingerprint manifest. "
            f"Use a new output directory or migrate the old run explicitly: {output_path}"
        )

    if not write_manifest:
        return manifest_path

    manifest = {
        "fingerprint": fingerprint,
        "framework_version": metadata.get("framework_version", "3.0.0"),
        "source_count": len(metadata.get("sources", [])),
        "config": metadata.get("config", {}),
        "runtime_settings": metadata.get("runtime_settings", {}),
        "model_routes": metadata.get("model_routes", {}),
        "sources": metadata.get("sources", []),
    }
    temp_path = manifest_path.with_suffix(".tmp")
    temp_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    temp_path.replace(manifest_path)
    return manifest_path


class CheckpointManager:
    """Manages checkpoints for pipeline resume capability."""
    
    def __init__(
        self,
        output_dir: str,
        run_fingerprint: str | None = None,
        run_metadata: Dict[str, Any] | None = None,
    ):
        """Initialize checkpoint manager.
        
        Args:
            output_dir: Base output directory for checkpoints
        """
        self.output_dir = Path(output_dir)
        checkpoint_root = self.output_dir / ".checkpoints"
        self.run_fingerprint = run_fingerprint
        self.checkpoint_dir = (
            checkpoint_root / run_fingerprint[:16]
            if run_fingerprint
            else checkpoint_root
        )
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        if run_fingerprint:
            (self.checkpoint_dir / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "fingerprint": run_fingerprint,
                        "metadata": run_metadata or {},
                    },
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                ),
                encoding="utf-8",
            )
        
        # Checkpoint file paths
        self.markdown_checkpoint = self.checkpoint_dir / "markdown_progress.json"
        self.chunks_checkpoint = self.checkpoint_dir / "chunks_progress.json"
        self.context_checkpoint = self.checkpoint_dir / "context_progress.json"
        self.qa_checkpoint = self.checkpoint_dir / "qa_progress.json"
        
        # In-memory state
        self._markdown_state = self._load_or_init(self.markdown_checkpoint, {
            'completed_files': [],
            'failed_files': [],
            'last_updated': None
        })
        self._chunks_state = self._load_or_init(self.chunks_checkpoint, {
            'completed_files': [],
            'chunks_by_file': {},
            'final_chunks_saved': False,
            'last_updated': None
        })
        self._context_state = self._load_or_init(self.context_checkpoint, {
            'completed_chunk_ids': [],
            'contexts': {},  # chunk_id -> context_result
            'last_updated': None
        })
        self._qa_state = self._load_or_init(self.qa_checkpoint, {
            'completed_chunk_ids': [],
            'successful_qa': [],
            'failed_qa': [],
            'chunks_with_context': [],
            'last_updated': None
        })
    
    def _load_or_init(self, path: Path, default: Dict) -> Dict:
        """Load a legacy snapshot and replay its append-only event journal."""
        state = default
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Failed to load checkpoint {path}: {e}")
        journal_path = path.with_suffix(".jsonl")
        if journal_path.exists():
            incomplete_tail = False
            with journal_path.open("r", encoding="utf-8") as handle:
                journal_lines = handle.readlines()
                for line_number, line in enumerate(journal_lines, 1):
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError as exc:
                        if line_number == len(journal_lines):
                            logging.warning(
                                "Ignoring incomplete checkpoint journal tail %s:%s",
                                journal_path,
                                line_number,
                            )
                            incomplete_tail = True
                            break
                        raise RuntimeError(
                            f"Checkpoint journal is corrupted at {journal_path}:{line_number}"
                        ) from exc
                    self._apply_event(state, event)
            if incomplete_tail:
                repair_path = journal_path.with_suffix(".repair.tmp")
                repair_path.write_text(
                    "".join(journal_lines[:-1]),
                    encoding="utf-8",
                )
                repair_path.replace(journal_path)
        return state

    @staticmethod
    def _apply_event(state: Dict, event: Dict) -> None:
        """Apply one idempotent checkpoint delta to an in-memory state."""
        operation = event.get("op")
        timestamp = event.get("timestamp") or datetime.now().isoformat()
        if operation == "markdown_complete":
            file_stem = str(event["file_stem"])
            if file_stem not in state["completed_files"]:
                state["completed_files"].append(file_stem)
        elif operation == "markdown_failed":
            failure = dict(event["failure"])
            if failure not in state["failed_files"]:
                state["failed_files"].append(failure)
        elif operation == "file_chunks":
            file_stem = str(event["file_stem"])
            state["chunks_by_file"][file_stem] = list(event.get("chunks", []))
            # New/repaired document chunks require a fresh combined-corpus write.
            # This also invalidates a stale final marker during journal replay.
            state["final_chunks_saved"] = False
            if file_stem not in state["completed_files"]:
                state["completed_files"].append(file_stem)
        elif operation == "final_chunks_saved":
            state["final_chunks_saved"] = True
        elif operation == "context":
            chunk_id = str(event["chunk_id"])
            if chunk_id not in state["completed_chunk_ids"]:
                state["completed_chunk_ids"].append(chunk_id)
                state["contexts"][chunk_id] = dict(event.get("context", {}))
        elif operation == "qa_result":
            chunk_id = str(event["chunk_id"])
            if chunk_id not in state["completed_chunk_ids"]:
                state["completed_chunk_ids"].append(chunk_id)
                state["successful_qa"].extend(event.get("successful", []))
                state["failed_qa"].extend(event.get("failed", []))
                context = event.get("chunk_with_context")
                if context:
                    state["chunks_with_context"].append(context)
        else:
            raise ValueError(f"Unknown checkpoint journal operation: {operation!r}")
        state["last_updated"] = timestamp

    def _append_event(self, path: Path, state: Dict, event: Dict) -> None:
        """Durably append one delta, then apply it to memory."""
        event = {**event, "timestamp": datetime.now().isoformat()}
        journal_path = path.with_suffix(".jsonl")
        try:
            with journal_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            logging.error("Failed to append checkpoint %s: %s", journal_path, exc)
            raise RuntimeError(
                f"Checkpoint write failed; stopping to preserve resumability: {journal_path}"
            ) from exc
        self._apply_event(state, event)
    
    def _save(self, path: Path, data: Dict):
        """Save checkpoint to file atomically."""
        data['last_updated'] = datetime.now().isoformat()
        temp_path = path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(path)  # Atomic rename
        except OSError as e:
            logging.error(f"Failed to save checkpoint {path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
            raise RuntimeError(
                f"Checkpoint write failed; stopping to preserve resumability: {path}"
            ) from e
    
    # =========================================================================
    # MARKDOWN CHECKPOINTS
    # =========================================================================
    
    def get_completed_markdown_files(self) -> Set[str]:
        """Get set of already converted markdown files (by stem name)."""
        return set(self._markdown_state.get('completed_files', []))
    
    def mark_markdown_complete(self, file_stem: str, md_path: str):
        """Mark a markdown file as successfully converted."""
        self._append_event(
            self.markdown_checkpoint,
            self._markdown_state,
            {"op": "markdown_complete", "file_stem": file_stem, "md_path": md_path},
        )
        print(f"   [SAVE] Checkpoint: Markdown saved for {file_stem}")
    
    def mark_markdown_failed(self, file_stem: str, error: str):
        """Mark a markdown conversion as failed."""
        failure = {
            'file': file_stem,
            'error': error,
            'timestamp': datetime.now().isoformat()
        }
        self._append_event(
            self.markdown_checkpoint,
            self._markdown_state,
            {"op": "markdown_failed", "failure": failure},
        )
    
    # =========================================================================
    # CHUNKING CHECKPOINTS
    # =========================================================================
    
    def get_completed_chunk_files(self) -> Set[str]:
        """Get set of already chunked files (by stem name)."""
        return set(self._chunks_state.get('completed_files', [])) & set(
            self.get_all_file_chunks()
        )
    
    def is_final_chunks_saved(self) -> bool:
        """Check if final renumbered chunks have been saved."""
        completed = set(self._chunks_state.get('completed_files', []))
        return bool(
            self._chunks_state.get('final_chunks_saved', False)
            and completed
            and completed == self.get_completed_chunk_files()
        )
    
    def save_file_chunks(self, file_stem: str, chunks: List[Dict]):
        """Save chunks for a single file (before renumbering)."""
        if not chunks or any(not chunk.get("content", "").strip() for chunk in chunks):
            raise ValueError(f"Cannot checkpoint empty chunks for {file_stem}")
        self._append_event(
            self.chunks_checkpoint,
            self._chunks_state,
            {"op": "file_chunks", "file_stem": file_stem, "chunks": chunks},
        )
        print(f"   [SAVE] Checkpoint: {len(chunks)} chunks saved for {file_stem}")
    
    def get_all_file_chunks(self) -> Dict[str, List[Dict]]:
        """Get all chunks organized by file."""
        # Older runs could journal zero chunks as a completed document.
        return {
            name: chunks
            for name, chunks in self._chunks_state.get('chunks_by_file', {}).items()
            if chunks and all(chunk.get("content", "").strip() for chunk in chunks)
        }
    
    def mark_final_chunks_saved(self):
        """Mark that final renumbered chunks have been saved."""
        self._append_event(
            self.chunks_checkpoint,
            self._chunks_state,
            {"op": "final_chunks_saved"},
        )
        print(f"   [SAVE] Checkpoint: Final chunks file saved")
    
    # =========================================================================
    # CONTEXT CHECKPOINTS
    # =========================================================================
    
    def get_completed_context_chunk_ids(self) -> Set[str]:
        """Get set of chunk IDs that have completed context building."""
        return set(self._context_state.get('completed_chunk_ids', []))
    
    def save_context(self, chunk_id: str, context_result: Dict):
        """Save context result for a chunk."""
        chunk_id_str = str(chunk_id)
        # Store a compact version of context (not the full chunks to save space)
        compact_context = {
            'status': context_result.get('status'),
            'depth': context_result.get('depth'),
            'hop_count': context_result.get('hop_count', 0),
            'chunks_added': context_result.get('chunks_added', []),
            'search_history': context_result.get('search_history', []),
            'termination_reason': context_result.get('termination_reason', '')
        }
        self._append_event(
            self.context_checkpoint,
            self._context_state,
            {"op": "context", "chunk_id": chunk_id_str, "context": compact_context},
        )
    
    def get_context(self, chunk_id: str) -> Optional[Dict]:
        """Get saved context for a chunk."""
        return self._context_state.get('contexts', {}).get(str(chunk_id))
    
    # =========================================================================
    # QA CHECKPOINTS
    # =========================================================================
    
    def get_completed_qa_chunk_ids(self) -> Set[str]:
        """Get set of chunk IDs that have completed QA generation."""
        return set(self._qa_state.get('completed_chunk_ids', []))
    
    def save_qa_result(self, chunk_id: str, successful: List[Dict], failed: List[Dict], 
                       chunk_with_context: Optional[Dict] = None):
        """Save QA generation result for a chunk."""
        chunk_id_str = str(chunk_id)
        self._append_event(
            self.qa_checkpoint,
            self._qa_state,
            {
                "op": "qa_result",
                "chunk_id": chunk_id_str,
                "successful": successful,
                "failed": failed,
                "chunk_with_context": chunk_with_context,
            },
        )
        
        success_count = len(successful)
        fail_count = len(failed)
        print(f"   [SAVE] Checkpoint: QA saved for chunk {chunk_id} ({success_count} pass, {fail_count} fail)")
    
    def get_accumulated_qa(self) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Get all accumulated QA results.
        
        Returns:
            Tuple of (successful_qa, failed_qa, chunks_with_context)
        """
        return (
            self._qa_state.get('successful_qa', []),
            self._qa_state.get('failed_qa', []),
            self._qa_state.get('chunks_with_context', [])
        )
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of checkpoint state."""
        return {
            'markdown': {
                'completed': len(self._markdown_state.get('completed_files', [])),
                'failed': len(self._markdown_state.get('failed_files', [])),
                'last_updated': self._markdown_state.get('last_updated')
            },
            'chunks': {
                'files_chunked': len(self._chunks_state.get('completed_files', [])),
                'final_saved': self._chunks_state.get('final_chunks_saved', False),
                'last_updated': self._chunks_state.get('last_updated')
            },
            'context': {
                'completed': len(self._context_state.get('completed_chunk_ids', [])),
                'last_updated': self._context_state.get('last_updated')
            },
            'qa': {
                'chunks_completed': len(self._qa_state.get('completed_chunk_ids', [])),
                'successful': len(self._qa_state.get('successful_qa', [])),
                'failed': len(self._qa_state.get('failed_qa', [])),
                'last_updated': self._qa_state.get('last_updated')
            }
        }
    
    def print_status(self):
        """Print checkpoint status."""
        summary = self.get_summary()
        
        print("\nCHECKPOINT STATUS")
        print("=" * 60)
        
        md = summary['markdown']
        if md['completed'] > 0 or md['failed'] > 0:
            print(f"   Markdown:  {md['completed']} completed, {md['failed']} failed")
        
        ch = summary['chunks']
        if ch['files_chunked'] > 0:
            status = "[OK] final saved" if ch['final_saved'] else "[...] in progress"
            print(f"   Chunks:    {ch['files_chunked']} files chunked ({status})")
        
        ctx = summary['context']
        if ctx['completed'] > 0:
            print(f"   Context:   {ctx['completed']} chunks completed")
        
        qa = summary['qa']
        if qa['chunks_completed'] > 0:
            print(f"   QA:        {qa['chunks_completed']} chunks, {qa['successful']} pass, {qa['failed']} fail")
        
        if all(v.get('completed', v.get('files_chunked', v.get('chunks_completed', 0))) == 0 
               for v in summary.values()):
            print("   No checkpoints found - starting fresh")
        
        print("=" * 60)
    
    def clear_all(self):
        """Clear all checkpoints (use with caution)."""
        for path in [self.markdown_checkpoint, self.chunks_checkpoint, 
                     self.context_checkpoint, self.qa_checkpoint]:
            for candidate in (path, path.with_suffix(".jsonl")):
                if candidate.exists():
                    candidate.unlink()
        
        # Reset in-memory state
        self._markdown_state = {'completed_files': [], 'failed_files': [], 'last_updated': None}
        self._chunks_state = {'completed_files': [], 'chunks_by_file': {}, 'final_chunks_saved': False, 'last_updated': None}
        self._context_state = {'completed_chunk_ids': [], 'contexts': {}, 'last_updated': None}
        self._qa_state = {'completed_chunk_ids': [], 'successful_qa': [], 'failed_qa': [], 'chunks_with_context': [], 'last_updated': None}
        
        print("All checkpoints cleared")
