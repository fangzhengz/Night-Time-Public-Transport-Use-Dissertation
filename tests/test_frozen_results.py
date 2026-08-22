from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_repository import validate  # noqa: E402


class FrozenResultTests(unittest.TestCase):
    def test_repository_evidence(self) -> None:
        self.assertGreaterEqual(len(validate()), 7)


if __name__ == "__main__":
    unittest.main()
