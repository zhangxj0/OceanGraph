"""Shared source-document discovery for corpus ingestion and preflight checks."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Collection, Iterable


DEFAULT_SOURCE_SUFFIXES = frozenset({".pdf", ".html", ".htm", ".txt", ".md", ".markdown"})
DEFAULT_IGNORED_FILENAMES = frozenset({"README.md", ".gitkeep"})


def discover_source_documents(
    input_dir: str | Path,
    *,
    supported_suffixes: Collection[str] = DEFAULT_SOURCE_SUFFIXES,
    ignored_filenames: Collection[str] = DEFAULT_IGNORED_FILENAMES,
    require_unique_stems: bool = False,
) -> list[Path]:
    """Return supported corpus files recursively in deterministic order.

    Recursive discovery allows both ``data/normalized/*.md`` and archives that
    unpack as ``data/normalized/normalized/*.md``.  The generation engine uses
    file stems as source identifiers, so it can request an explicit collision
    check before writing checkpoints and Markdown intermediates.
    """

    root = Path(input_dir)
    if not root.is_dir():
        return []

    suffixes = {str(suffix).lower() for suffix in supported_suffixes}
    ignored = {str(name) for name in ignored_filenames}
    documents = sorted(
        (
            path
            for path in root.rglob("*")
            if path.is_file()
            and path.name not in ignored
            and path.suffix.lower() in suffixes
        ),
        key=lambda path: path.relative_to(root).as_posix().lower(),
    )

    if require_unique_stems:
        by_stem: dict[str, list[Path]] = defaultdict(list)
        for path in documents:
            by_stem[path.stem].append(path)
        collisions = {
            stem: paths for stem, paths in by_stem.items() if len(paths) > 1
        }
        if collisions:
            details = "; ".join(
                f"{stem}: {', '.join(str(path.relative_to(root)) for path in paths)}"
                for stem, paths in sorted(collisions.items())
            )
            raise ValueError(
                "Source filenames must have unique stems because stems are used "
                f"as checkpoint identifiers. Rename the conflicting files: {details}"
            )

    return documents


def count_source_types(documents: Iterable[Path]) -> dict[str, int]:
    """Count discovered documents using the categories shown by preflight."""

    counts = {"pdf": 0, "html": 0, "text": 0}
    for path in documents:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            counts["pdf"] += 1
        elif suffix in {".html", ".htm"}:
            counts["html"] += 1
        else:
            counts["text"] += 1
    return counts


__all__ = [
    "DEFAULT_IGNORED_FILENAMES",
    "DEFAULT_SOURCE_SUFFIXES",
    "count_source_types",
    "discover_source_documents",
]
