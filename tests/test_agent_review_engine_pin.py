"""Regression coverage for reusable Sentinel engine pinning."""
from __future__ import annotations

import re
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "agent-review.yml"


class AgentReviewEnginePinTests(unittest.TestCase):
    def test_all_engine_checkouts_use_one_full_commit_sha(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        refs = re.findall(
            r"repository: Aftergraph/\.github\s*\n\s*ref: ([0-9a-f]{40})\b",
            workflow,
        )
        self.assertGreaterEqual(len(refs), 3)
        self.assertEqual(len(set(refs)), 1)

    def test_engine_checkouts_never_follow_mutable_refs(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        blocks = re.findall(
            r"repository: Aftergraph/\.github\s*\n\s*ref: ([^\s#]+)",
            workflow,
        )
        self.assertTrue(blocks)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in blocks))


if __name__ == "__main__":
    unittest.main()
