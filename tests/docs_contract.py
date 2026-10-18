"""Shared import-safe documentation checker, used by tests and the quality gate."""

import runpy
from pathlib import Path

ROOT = Path(__file__).parents[1]
CHECKER = runpy.run_path(str(ROOT / "scripts/check-docs.py"))
