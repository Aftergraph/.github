from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit_runner_policy.py"
spec = importlib.util.spec_from_file_location("audit_runner_policy", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

class RunnerPolicyAuditTests(unittest.TestCase):
    def test_cancel_true_is_error(self) -> None:
        findings = module.scan_workflow_text("x.yml", "concurrency:\n  cancel-in-progress: true\n")
        self.assertTrue(any(f["code"] == "false-red-cancellation" and f["severity"] == "error" for f in findings))

    def test_modern_workflow_is_clean(self) -> None:
        findings = module.scan_workflow_text("x.yml", "uses: actions/checkout@v7\ncancel-in-progress: false\n")
        self.assertEqual(findings, [])

    def test_checkout_v4_is_warning(self) -> None:
        findings = module.scan_workflow_text("x.yml", "uses: actions/checkout@v4\n")
        self.assertEqual(findings[0]["severity"], "warning")

    def test_non_cancelling_pr_scoped_group_is_error(self) -> None:
        text = """concurrency:
  group: verify-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: false
"""
        findings = module.scan_workflow_text("x.yml", text)
        self.assertTrue(any(f["code"] == "cross-sha-serialization" for f in findings))

    def test_sha_scoped_group_is_allowed(self) -> None:
        text = """concurrency:
  group: verify-${{ github.event.pull_request.head.sha || github.sha }}
  cancel-in-progress: false
"""
        findings = module.scan_workflow_text("x.yml", text)
        self.assertFalse(any(f["code"] == "cross-sha-serialization" for f in findings))

if __name__ == "__main__":
    unittest.main()
