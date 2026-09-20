from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_runner_fabric.py"

spec = importlib.util.spec_from_file_location("verify_runner_fabric", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

class RunnerFabricTests(unittest.TestCase):
    def test_contract(self) -> None:
        self.assertEqual(module.verify(), [])

if __name__ == "__main__":
    unittest.main()
