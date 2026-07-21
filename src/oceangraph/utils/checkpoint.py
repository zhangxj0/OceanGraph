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
INPUT_SUFFIXES = {".pdf", ".html", ".htm", ".txt", ".md", ".markdown", ".json"}


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
    framework_version: str = "2.2.1",
) -> Tuple[str, Dict[str, Any]]:
    """Hash configuration and corpus contents used by a resumable run."""
    source_files: List[Path] = []
    if input_chunks_file and Path(input_chunks_file).is_file():
        source_files = [Path(input_chunks_file).resolve()]
        source_root = source_files[0].parent
    elif input_dir and Path(input_dir).is_dir():
        source_root = Path(input_dir).resolve()
        source_files = sorted(
            path.resolve()
            for path in source_root.rglob("*")
            if path.is_file()
            and path.suffix.casefold() in INPUT_SUFFIXES
            and path.name not in {"README.md", ".gitkeep"}
        )
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
        "config": _safe_config(config),
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
) -> Path:
    """Refuse to mix artifacts produced from a different config or corpus."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    manifest_path = output_path / RUN_MANIFEST_NAME
    existing = None
    if manifest_path.exists():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"Cannot read existing run manifest: {manifest_path}") from exc

    if existing and existing.get("fingerprint") != fingerprint:
        raise RuntimeError(
            "Output directory belongs to a different OceanGraph corpus/configuration. "
            f"Use a new output directory instead of mixing artifacts: {output_path}"
        )
    if existing is None and any((output_path / name).exists() for name in MATERIAL_OUTPUTS):
        raise RuntimeError(
            "Existing OceanGraph artifacts have no v2.2.1 fingerprint manifest. "
            f"Use a new output directory or migrate the old run explicitly: {output_path}"
        )

    manifest = {
        "fingerprint": fingerprint,
        "framework_version": metadata.get("framework_version", "2.2.1"),
        "source_count": len(metadata.get("sources", [])),
        "config": metadata.get("config", {}),
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
        """Load checkpoint from file or return default."""
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logging.warning(f"Failed to load checkpoint {path}: {e}")
        return default
    
    def _save(self, path: Path, data: Dict):
        """Save checkpoint to file atomically."""
        data['last_updated'] = datetime.now().isoformat()
        temp_path = path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path.replace(path)  # Atomic rename
        except IOError as e:
            logging.error(f"Failed to save checkpoint {path}: {e}")
            if temp_path.exists():
                temp_path.unlink()
    
    # =========================================================================
    # MARKDOWN CHECKPOINTS
    # =========================================================================
    
    def get_completed_markdown_files(self) -> Set[str]:
        """Get set of already converted markdown files (by stem name)."""
        return set(self._markdown_state.get('completed_files', []))
    
    def mark_markdown_complete(self, file_stem: str, md_path: str):
        """Mark a markdown file as successfully converted."""
        if file_stem not in self._markdown_state['completed_files']:
            self._markdown_state['completed_files'].append(file_stem)
        self._save(self.markdown_checkpoint, self._markdown_state)
        print(f"   [SAVE] Checkpoint: Markdown saved for {file_stem}")
    
    def mark_markdown_failed(self, file_stem: str, error: str):
        """Mark a markdown conversion as failed."""
        self._markdown_state['failed_files'].append({
            'file': file_stem,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
        self._save(self.markdown_checkpoint, self._markdown_state)
    
    # =========================================================================
    # CHUNKING CHECKPOINTS
    # =========================================================================
    
    def get_completed_chunk_files(self) -> Set[str]:
        """Get set of already chunked files (by stem name)."""
        return set(self._chunks_state.get('completed_files', []))
    
    def is_final_chunks_saved(self) -> bool:
        """Check if final renumbered chunks have been saved."""
        return self._chunks_state.get('final_chunks_saved', False)
    
    def save_file_chunks(self, file_stem: str, chunks: List[Dict]):
        """Save chunks for a single file (before renumbering)."""
        if file_stem not in self._chunks_state['completed_files']:
            self._chunks_state['completed_files'].append(file_stem)
        self._chunks_state['chunks_by_file'][file_stem] = chunks
        self._save(self.chunks_checkpoint, self._chunks_state)
        print(f"   [SAVE] Checkpoint: {len(chunks)} chunks saved for {file_stem}")
    
    def get_all_file_chunks(self) -> Dict[str, List[Dict]]:
        """Get all chunks organized by file."""
        return self._chunks_state.get('chunks_by_file', {})
    
    def mark_final_chunks_saved(self):
        """Mark that final renumbered chunks have been saved."""
        self._chunks_state['final_chunks_saved'] = True
        self._save(self.chunks_checkpoint, self._chunks_state)
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
        if chunk_id_str not in self._context_state['completed_chunk_ids']:
            self._context_state['completed_chunk_ids'].append(chunk_id_str)
        
        # Store a compact version of context (not the full chunks to save space)
        compact_context = {
            'status': context_result.get('status'),
            'depth': context_result.get('depth'),
            'hop_count': context_result.get('hop_count', 0),
            'chunks_added': context_result.get('chunks_added', []),
            'search_history': context_result.get('search_history', []),
            'termination_reason': context_result.get('termination_reason', '')
        }
        self._context_state['contexts'][chunk_id_str] = compact_context
        self._save(self.context_checkpoint, self._context_state)
    
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
        if chunk_id_str not in self._qa_state['completed_chunk_ids']:
            self._qa_state['completed_chunk_ids'].append(chunk_id_str)
        
        # Append to lists
        self._qa_state['successful_qa'].extend(successful)
        self._qa_state['failed_qa'].extend(failed)
        if chunk_with_context:
            self._qa_state['chunks_with_context'].append(chunk_with_context)
        
        self._save(self.qa_checkpoint, self._qa_state)
        
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
            if path.exists():
                path.unlink()
        
        # Reset in-memory state
        self._markdown_state = {'completed_files': [], 'failed_files': [], 'last_updated': None}
        self._chunks_state = {'completed_files': [], 'chunks_by_file': {}, 'final_chunks_saved': False, 'last_updated': None}
        self._context_state = {'completed_chunk_ids': [], 'contexts': {}, 'last_updated': None}
        self._qa_state = {'completed_chunk_ids': [], 'successful_qa': [], 'failed_qa': [], 'chunks_with_context': [], 'last_updated': None}
        
        print("All checkpoints cleared")
