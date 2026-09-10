#!/usr/bin/env python3
"""Slice-3 tests (TDD RED first): AVC override, merge_group, push audit, docs.

Contracts under test (from v4-execution/agent-review-decisions.md D1/D3):
  AVC has an EMPTY pin set. Empty must stay BLOCKED (reason EMPTY_PIN_SET)
  unless the explicit owner-override label OWNER_OVERRIDE_ACCEPT_RISK is
  present, in which case the verdict is MERGEABLE with the override recorded
  in reason_codes (never a silent pass). Delta mismatch still BLOCKED.
  Override never bypasses pinned-check failures on other repos.
  Workflow supports merge_group + push-to-main audit (detective).
  Agent stays COMMENT-only permanently and posts NOTHING (emit only).
Stdlib unittest only.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "scripts" / "agent_review.py"
AUDIT = ROOT / "scripts" / "audit_push.py"
POLICY = ROOT / "policies" / "pinned-checks.json"
WORKFLOW = ROOT / ".github" / "workflows" / "agent-review.yml"
ACTION = ROOT / "actions" / "agent-review" / "action.yml"
DOCS = ROOT / "docs" / "agent-review.md"
FIXTURE = ROOT / "tests" / "fixtures" / "tg83-da5d934.json"

OVERRIDE = "OWNER_OVERRIDE_ACCEPT_RISK"

D1_EXPECTED = {
    "trust-gateway": ["test", "gate / integration", "Analyze (javascript)",
                      "CodeQL"],
    "aie": ["test (3.11)", "test (3.12)", "test (3.13)", "Analyze (python)",
            "CodeQL"],
    "studio": ["Monolithic Release Verification (18 Gates)",
               "Analyze (javascript)", "CodeQL"],
    "works-execution": ["test", "Analyze (go)", "CodeQL"],
    "wi-backend": ["test (3.11)", "test (3.12)", "Analyze (python)",
                   "production-container-smoke", "CodeQL"],
    "runtime": ["build-test"],
    "model-registry": ["validate"],
    "autonomous-venture-company": [],
}

HEAD_A = "a" * 40
HEAD_B = "b" * 40


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def avc_packet():
    packet = load_fixture()
    packet["repo"] = "autonomous-venture-company"
    packet["number"] = 1
    packet["url"] = ("https://github.com/Aftergraph/"
                     "autonomous-venture-company/pull/1")
    packet["head_sha"] = HEAD_A
    return packet


def run_agent(packet_doc, current_head, checks_doc, labels=None,
              run_id="slice3-test"):
    """Run agent script; labels is a list of label-name strings."""
    with tempfile.TemporaryDirectory() as tmp:
        packet_path = Path(tmp) / "packet.json"
        checks_path = Path(tmp) / "checks.json"
        packet_path.write_text(json.dumps(packet_doc), encoding="utf-8")
        checks_path.write_text(json.dumps(checks_doc), encoding="utf-8")
        cmd = [sys.executable, str(AGENT),
               "--packet", str(packet_path),
               "--current-head", current_head,
               "--checks", str(checks_path),
               "--policy", str(POLICY),
               "--agent-name", "agent-review",
               "--agent-version", "0.3.0",
               "--run-id", run_id]
        if labels is not None:
            cmd += ["--labels", ",".join(labels)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, proc.stdout, proc.stderr


def run_audit(head_sha, prs_doc, run_id="audit-test"):
    with tempfile.TemporaryDirectory() as tmp:
        prs_path = Path(tmp) / "prs.json"
        if isinstance(prs_doc, str):
            prs_path.write_text(prs_doc, encoding="utf-8")
        else:
            prs_path.write_text(json.dumps(prs_doc), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(AUDIT),
             "--head-sha", head_sha,
             "--associated-prs", str(prs_path),
             "--run-id", run_id],
            capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, proc.stdout, proc.stderr


class PolicyFullPinSetTest(unittest.TestCase):
    def test_t6_policy_matches_d1_full_pin_set(self):
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertEqual(set(policy["checks"].keys()), set(D1_EXPECTED.keys()))
        for repo, names in D1_EXPECTED.items():
            self.assertEqual(sorted(policy["checks"][repo]), sorted(names),
                             repo)
        self.assertEqual(policy["checks"]["autonomous-venture-company"], [])


class AvcPrivateModeTest(unittest.TestCase):
    def test_t6a_avc_empty_pin_set_stays_blocked(self):
        packet = avc_packet()
        rc, out, err = run_agent(packet, HEAD_A, {"checks": []}, labels=[])
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("EMPTY_PIN_SET", agent["reason_codes"])
        # Never a silent pass: a BLOCKED verdict must carry reasons.
        self.assertTrue(agent["reason_codes"])

    def test_t6b_avc_owner_override_is_explicit_mergeable(self):
        packet = avc_packet()
        rc, out, err = run_agent(packet, HEAD_A, {"checks": []},
                                 labels=[OVERRIDE])
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "MERGEABLE")
        self.assertIn(OVERRIDE, agent["reason_codes"])

    def test_t6c_avc_unrelated_label_stays_blocked(self):
        packet = avc_packet()
        rc, out, err = run_agent(packet, HEAD_A, {"checks": []},
                                 labels=["some-other-label"])
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("EMPTY_PIN_SET", agent["reason_codes"])
        self.assertNotIn(OVERRIDE, agent["reason_codes"])

    def test_t6d_override_never_bypasses_pinned_failures(self):
        packet = load_fixture()
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        names = policy["checks"][packet["repo"]]
        checks = {"checks": [
            {"name": n, "status": "COMPLETED", "conclusion": "SUCCESS"}
            for n in names[1:]]}  # first pinned check missing
        rc, out, err = run_agent(packet, packet["head_sha"], checks,
                                 labels=[OVERRIDE])
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("PINNED_CHECK_MISSING", agent["reason_codes"])

    def test_t6e_avc_override_with_delta_mismatch_stays_blocked(self):
        packet = avc_packet()
        rc, out, err = run_agent(packet, HEAD_B, {"checks": []},
                                 labels=[OVERRIDE])
        # current head != reviewed head: delta mismatch blocks regardless.
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertFalse(agent["delta_clean"])
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("DELTA_MISMATCH", agent["reason_codes"])


class MergeGroupTriggerTest(unittest.TestCase):
    def test_t7_workflow_supports_merge_group(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("merge_group:", text)
        self.assertIn("checks_requested", text)

    def test_t7b_audit_job_gated_to_push_only(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("push-audit", text)
        self.assertIn("github.event_name == 'push'", text)
        self.assertIn("branches:", text)
        self.assertIn("main", text)


class PushAuditScriptTest(unittest.TestCase):
    def test_t8a_pr_associated_head_passes(self):
        prs = [{"number": 12,
                "url": "https://github.com/Aftergraph/.github/pull/12"}]
        rc, out, err = run_audit(HEAD_A, prs)
        self.assertEqual(rc, 0, err)
        doc = json.loads(out)
        self.assertEqual(doc["head_sha"], HEAD_A)
        self.assertTrue(doc["pr_associated"])
        self.assertEqual(doc["verdict"], "AUDIT_PASS")

    def test_t8b_direct_push_fails_visibly_with_finding(self):
        rc, out, err = run_audit(HEAD_A, [])
        self.assertNotEqual(rc, 0)
        doc = json.loads(out)
        self.assertEqual(doc["head_sha"], HEAD_A)
        self.assertFalse(doc["pr_associated"])
        self.assertEqual(doc["verdict"], "AUDIT_FAIL")
        self.assertTrue(str(doc.get("finding", "")).strip())

    def test_t8c_bad_sha_is_tool_error(self):
        rc, out, err = run_audit("not-a-sha", [])
        self.assertEqual(rc, 2)
        self.assertIn("head-sha", err.lower())


class DocsOperatorGuideTest(unittest.TestCase):
    def test_t9_docs_cover_triggers_verdicts_override_risks(self):
        self.assertTrue(DOCS.exists(), "docs/agent-review.md must exist")
        text = DOCS.read_text(encoding="utf-8")
        for needle in ["merge_group", "MERGEABLE", "BLOCKED",
                       OVERRIDE, "EMPTY_PIN_SET", "push",
                       "detective", "COMMENT"]:
            self.assertIn(needle, text, needle)
        lowered = text.lower()
        self.assertIn("non-preventive", lowered)
        self.assertTrue("forc" in lowered and "push" in lowered)


class CommentOnlyTest(unittest.TestCase):
    POST_TOKENS = ["gh pr comment", "gh pr review", "gh issue comment",
                   "createComment", "submitReview", "pull-requests: write",
                   "issues: write"]

    def test_t10_workflow_and_action_post_nothing(self):
        for path in (WORKFLOW, ACTION):
            text = path.read_text(encoding="utf-8")
            for token in self.POST_TOKENS:
                self.assertNotIn(token, text, f"{path.name}: {token}")

    def test_t10b_scripts_emit_only_no_posting_calls(self):
        for path in (AGENT, AUDIT):
            text = path.read_text(encoding="utf-8")
            for token in ["gh pr comment", "gh pr review", "createComment",
                          "submitReview", "urllib.request.urlopen",
                          "requests.post"]:
                self.assertNotIn(token, text, f"{path.name}: {token}")


if __name__ == "__main__":
    unittest.main()
