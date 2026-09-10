#!/usr/bin/env python3
"""Tests for scripts/agent_review.py — slice 1 (READ-ONLY) stdlib unittest.

Contract under test:
  C1 delta-vs-reviewed-head: current head_sha vs reviewed/packet head_sha.
     Mismatch => BLOCKED + DELTA_MISMATCH.
  C2 pinned-checks gate: policies/pinned-checks.json per-repo named checks.
     Missing/pending => BLOCKED.
  Output: 14-field review packet PLUS additive `agent_review` block, JSON to
  stdout only. Exit 0 whenever a packet is emitted; non-zero only on tool
  errors (bad args, unreadable files, malformed SHA).
"""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "scripts" / "agent_review.py"
FIXTURE = ROOT / "tests" / "fixtures" / "tg83-da5d934.json"
POLICY = ROOT / "policies" / "pinned-checks.json"
SCHEMA = ROOT / "schemas" / "review-packet.schema.json"

# The 14 packet fields from after-graph-governance PR #144
# docs/evidence/sole-maintainer-merge-window-2026-09-10.json.
PACKET_FIELDS_14 = [
    "repo", "number", "url", "title", "head_sha", "head_branch", "base",
    "mergeable", "merge_state", "review_decision", "diffstat", "checks",
    "reviews", "all_required_checks_green",
]

AGENT_FIELDS_8 = [
    "name", "version", "run_id", "reviewed_head_sha", "current_head_sha",
    "delta_clean", "verdict", "reason_codes",
]


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def load_policy():
    return json.loads(POLICY.read_text(encoding="utf-8"))


def green_checks(names):
    return {
        "checks": [
            {"name": n, "status": "COMPLETED", "conclusion": "SUCCESS"}
            for n in names
        ]
    }


def run_agent(packet_doc, current_head, checks_doc, run_id="test-run-1"):
    """Run the agent script on temp files; return (returncode, stdout, stderr)."""
    with tempfile.TemporaryDirectory() as tmp:
        packet_path = Path(tmp) / "packet.json"
        checks_path = Path(tmp) / "checks.json"
        packet_path.write_text(json.dumps(packet_doc), encoding="utf-8")
        checks_path.write_text(json.dumps(checks_doc), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(AGENT),
             "--packet", str(packet_path),
             "--current-head", current_head,
             "--checks", str(checks_path),
             "--policy", str(POLICY),
             "--agent-name", "agent-review",
             "--agent-version", "0.1.0",
             "--run-id", run_id],
            capture_output=True, text=True, cwd=ROOT,
        )
        return proc.returncode, proc.stdout, proc.stderr


class C1DeltaTest(unittest.TestCase):
    def test_t1_heads_match_pinned_green_is_mergeable(self):
        packet = load_fixture()
        policy = load_policy()
        names = policy["checks"][packet["repo"]]
        rc, out, err = run_agent(packet, packet["head_sha"], green_checks(names))
        self.assertEqual(rc, 0, err)
        doc = json.loads(out)
        agent = doc["agent_review"]
        self.assertTrue(agent["delta_clean"])
        self.assertEqual(agent["verdict"], "MERGEABLE")
        self.assertEqual(agent["reason_codes"], [])
        self.assertEqual(agent["reviewed_head_sha"], packet["head_sha"])
        self.assertEqual(agent["current_head_sha"], packet["head_sha"])


class C1MismatchTest(unittest.TestCase):
    def test_t2_mutated_head_is_blocked_delta(self):
        packet = load_fixture()
        policy = load_policy()
        names = policy["checks"][packet["repo"]]
        mutated = packet["head_sha"][:-1] + (
            "0" if packet["head_sha"][-1] != "0" else "1")
        rc, out, err = run_agent(packet, mutated, green_checks(names))
        self.assertEqual(rc, 0, err)
        doc = json.loads(out)
        agent = doc["agent_review"]
        self.assertFalse(agent["delta_clean"])
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("DELTA_MISMATCH", agent["reason_codes"])
        self.assertEqual(agent["current_head_sha"], mutated)


class C2PinnedChecksTest(unittest.TestCase):
    def test_t3_pending_pinned_check_is_blocked(self):
        packet = load_fixture()
        policy = load_policy()
        names = policy["checks"][packet["repo"]]
        checks = green_checks(names)
        checks["checks"][0] = {
            "name": names[0], "status": "IN_PROGRESS", "conclusion": None,
        }
        rc, out, err = run_agent(packet, packet["head_sha"], checks)
        self.assertEqual(rc, 0, err)
        doc = json.loads(out)
        agent = doc["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("PINNED_CHECK_PENDING", agent["reason_codes"])

    def test_t3_missing_pinned_check_is_blocked(self):
        packet = load_fixture()
        policy = load_policy()
        names = policy["checks"][packet["repo"]]
        checks = green_checks(names[1:])
        rc, out, err = run_agent(packet, packet["head_sha"], checks)
        self.assertEqual(rc, 0, err)
        doc = json.loads(out)
        agent = doc["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("PINNED_CHECK_MISSING", agent["reason_codes"])


class SchemaCompatTest(unittest.TestCase):
    def test_t5_schema_backward_compat(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        # The schema requires exactly the original 14 fields; the additive
        # agent block must NOT be required so old readers keep working.
        self.assertEqual(sorted(schema["required"]), sorted(PACKET_FIELDS_14))
        self.assertIn("agent_review", schema["properties"])
        self.assertNotIn("agent_review", schema["required"])

    def test_t5_old_reader_ignores_agent_block(self):
        packet = load_fixture()
        policy = load_policy()
        names = policy["checks"][packet["repo"]]
        rc, out, err = run_agent(packet, packet["head_sha"], green_checks(names))
        self.assertEqual(rc, 0, err)
        new_doc = json.loads(out)
        # Simulated old reader: knows only the original 14 fields.
        old_view = {k: new_doc[k] for k in PACKET_FIELDS_14}
        self.assertEqual(old_view, packet)
        # And the additive block carries exactly the 8 specified fields.
        self.assertEqual(
            sorted(new_doc["agent_review"].keys()), sorted(AGENT_FIELDS_8))


if __name__ == "__main__":
    unittest.main()
