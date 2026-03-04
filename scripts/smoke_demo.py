#!/usr/bin/env python
"""Run a lightweight smoke test for demo reset behaviour.

This script is intended for CI and exits non-zero on failure.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    # Keep Qt bootstrap deterministic in headless CI environments.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    suite = unittest.defaultTestLoader.loadTestsFromName("tests.test_demo_reset")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
