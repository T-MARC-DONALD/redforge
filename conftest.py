"""Pytest bootstrap: make redforge importable from a plain checkout.

pytest is launched in-process (python -m pytest), so this file runs before
any test module imports and puts .deps/ + the project root on sys.path.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(ROOT, ".deps"), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
