#!/usr/bin/env python3
"""Run the OceanGraph-R1 multi-agent dataset generation pipeline."""

from __future__ import annotations

import os
import sys


ROOT = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(ROOT, "src"))

from oceangraph.cli import main


if __name__ == "__main__":
    main()

