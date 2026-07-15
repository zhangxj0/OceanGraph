#!/usr/bin/env python3
"""Convert OceanGraph-R1 QA output into Search-R1 training files."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from oceangraph_search_r1 import main


def _ensure_default(flag: str, value: str) -> None:
    if flag not in sys.argv[1:]:
        sys.argv.extend([flag, value])


if __name__ == "__main__":
    if "--help" not in sys.argv and "-h" not in sys.argv:
        _ensure_default("--data-source", "oceangraph_ocean")
        _ensure_default("--wiki-output-name", "oceangraph_2wiki_like.jsonl")
        _ensure_default("--id-prefix", "oceangraph")
    raise SystemExit(main())
