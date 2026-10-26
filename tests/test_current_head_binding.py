"""C3 regression: superseded historical approvals must not veto a valid new review.

This test imports the real Sentinel engine, not a rewritten stand-in.
"""
import importlib.util
import unittest
from pathlib import Path

AGENT = Path(__file__).resolve().parents[1] / "scripts" / "agent_review.py"
spec = importlib.util.spec_from_file_location("agent_review_under_test", AGENT)
assert spec is not None and spec.loader is not None
review = importlib.util.module_from_spec(spec)
spec.loader.exec_module(review)

PUSH = "2026-10-26T20:32:00Z"


def binding(approvals, **overrides):
    result = {
        "head_commit_pushed_at": PUSH,
        "reviews": [{"state": "APPROVED", "author": "github-actions[bot]",
                     "submitted_at": timestamp} for timestamp in approvals],
        "unresolved_conversations": 0,
        "codeowners_independent_possible": False,
        "codeowners_matched": False,
    }
    result.update(overrides)
    return result


class CurrentHeadApprovalBindingTests(unittest.TestCase):
    def test_superseded_approval_does_not_veto_new_valid_approval(self):
        self.assertEqual([], review.check_binding(binding([
            "2026-10-26T11:28:26Z",
            "2026-10-26T20:33:02Z",
        ])))

    def test_single_earlier_approval_still_blocks(self):
        self.assertIn("PUSH_AFTER_REVIEW", review.check_binding(
            binding(["2026-10-26T11:28:26Z"])))

    def test_all_approvals_predate_push_still_blocks(self):
        self.assertIn("PUSH_AFTER_REVIEW", review.check_binding(
            binding(["2026-10-26T10:00:00Z", "2026-10-26T11:28:26Z"])))

    def test_missing_or_invalid_timestamp_stays_fail_closed(self):
        for value in [None, "", "not-a-time"]:
            with self.subTest(value=value):
                self.assertIn("REVIEW_BINDING_UNKNOWN", review.check_binding(
                    binding([value])))

    def test_one_valid_and_one_unknown_review_stays_fail_closed(self):
        self.assertIn("REVIEW_BINDING_UNKNOWN", review.check_binding(
            binding([None, "2026-10-26T20:33:02Z"])))

    def test_unknown_push_time_stays_blocked(self):
        self.assertIn("REVIEW_BINDING_UNKNOWN", review.check_binding(
            binding(["2026-10-26T20:33:02Z"],
                    head_commit_pushed_at=None)))

    def test_unresolved_conversations_still_block_after_fresh_approval(self):
        self.assertIn("UNRESOLVED_CONVERSATIONS", review.check_binding(
            binding(["2026-10-26T20:33:02Z"],
                    unresolved_conversations=1)))

    def test_matching_independent_codeowner_still_required(self):
        self.assertIn("CODEOWNERS_UNMATCHED", review.check_binding(
            binding(["2026-10-26T20:33:02Z"],
                    codeowners_independent_possible=True,
                    codeowners_matched=False)))


if __name__ == "__main__":
    unittest.main()
