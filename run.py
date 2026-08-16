"""redforge bootstrap - run the toolkit from a plain checkout.

Third-party dependencies live in .deps/ (installed with pip --target), so
the project is self-contained and needs no global install. This file puts
.deps/ and the project root on sys.path, then hands off to the CLI.

Usage:
    python run.py --help
    python run.py run --config examples/configs/example_config.yaml --provider mock
    python run.py smoke
    python run.py list
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
DEPS = os.path.join(ROOT, ".deps")

for _p in (DEPS, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from redforge.cli import app  # noqa: E402

if __name__ == "__main__":
    app()
