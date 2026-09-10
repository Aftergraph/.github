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
AIE_FIXTURE = ROOT / "tests" / "fixtures" / "aie70-032f425.json"
AVC_FIXTURE = ROOT / "tests" / "fixtures" / "avc1021-ed5c072.json"
POLICY = ROOT / "policies" / "pinned-checks.json"
SEAM_RULES = ROOT / "policies" / "seam-rules.json"
SCHEMA = ROOT / "schemas" / "review-packet.schema.json"
ACTION = ROOT / "actions" / "agent-review" / "action.yml"
WORKFLOW = ROOT / ".github" / "workflows" / "agent-review.yml"

# Full per-repo pinned table from agent-review-decisions.md D1.
# AVC stays [] (no CI): fail closed unless OWNER_OVERRIDE_ACCEPT_RISK is present.
EXPECTED_PINNED_CHECKS = {
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

OVERRIDE_LABEL = "OWNER_OVERRIDE_ACCEPT_RISK"


def run_audit(prs_doc, run_id="test-audit-1"):
    """Run the agent script in --audit-push mode; return (rc, stdout, stderr)."""
    with tempfile.TemporaryDirectory() as tmp:
        prs_path = Path(tmp) / "prs.json"
        prs_path.write_text(json.dumps(prs_doc), encoding="utf-8")
        cmd = [sys.executable, str(AGENT),
               "--audit-push", "0" * 40,
               "--prs", str(prs_path),
               "--run-id", run_id]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        return proc.returncode, proc.stdout, proc.stderr

PUSHED_AT = "2026-09-10T08:00:00Z"
NOW = "2026-09-10T12:00:00Z"

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


def run_agent(packet_doc, current_head, checks_doc, run_id="test-run-1",
              binding=None, seams=None, emit_dir=None, now=NOW):
    """Run the agent script on temp files; return (returncode, stdout, stderr)."""
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
               "--agent-version", "0.2.0",
               "--run-id", run_id]
        if binding is not None:
            binding_path = Path(tmp) / "binding.json"
            binding_path.write_text(json.dumps(binding), encoding="utf-8")
            cmd += ["--binding", str(binding_path)]
        if seams is not None:
            seams_path = Path(tmp) / "seams.json"
            seams_path.write_text(json.dumps(seams), encoding="utf-8")
            cmd += ["--seams", str(seams_path),
                    "--seam-rules", str(SEAM_RULES),
                    "--now", now]
        out_dir = Path(emit_dir) if emit_dir is not None else Path(tmp) / "out"
        if emit_dir is not None:
            cmd += ["--emit-dir", str(out_dir)]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
        emitted = sorted(p.name for p in out_dir.glob("*.json")) \
            if out_dir.is_dir() else []
        return proc.returncode, proc.stdout, proc.stderr, out_dir, emitted


def run_agent_v1(packet_doc, current_head, checks_doc, run_id="test-run-1"):
    """Slice-1 calling convention (no slice-2 flags); keeps old tests intact."""
    rc, out, err, _out_dir, _emitted = run_agent(
        packet_doc, current_head, checks_doc, run_id=run_id)
    return rc, out, err


def make_binding(pushed_at=PUSHED_AT, reviews=(), unresolved=0,
                 codeowners=True, labels=()):
    return {
        "head_commit_pushed_at": pushed_at,
        "reviews": list(reviews),
        "unresolved_conversations": unresolved,
        "codeowners_matched": codeowners,
        "labels": list(labels),
    }


def make_approval(author="JonasAbde", submitted_at="2026-09-10T09:00:00Z"):
    return {"author": author, "state": "APPROVED",
            "submitted_at": submitted_at}


def green_binding():
    """Binding with nothing to object to and no approvals to invalidate."""
    return make_binding()


def make_seams(cited_ids=(), ledger=None, records=(), contract_pins=None,
               new_identifiers=(), memory_authority_claims=()):
    return {
        "cited_ids": list(cited_ids),
        "ledger": dict(ledger or {}),
        "records": list(records),
        "contract_pins": dict(contract_pins or {}),
        "new_identifiers": list(new_identifiers),
        "memory_authority_claims": list(memory_authority_claims),
    }


def good_record(**over):
    rec = {
        "genesis": {"subject": "s", "purpose": "p", "tenant": "t"},
        "identity": {"ids": ["id-1"], "lineage": None,
                     "timestamp": "2026-09-10T07:00:00Z"},
        "expires_at": None,
        "evidence": "evidence:ledger/CON-001",
    }
    rec.update(over)
    return rec


class C1DeltaTest(unittest.TestCase):
    def test_t1_heads_match_pinned_green_is_mergeable(self):
        packet = load_fixture()
        policy = load_policy()
        names = policy["checks"][packet["repo"]]
        rc, out, err = run_agent_v1(packet, packet["head_sha"], green_checks(names))
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
        rc, out, err = run_agent_v1(packet, mutated, green_checks(names))
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
        rc, out, err = run_agent_v1(packet, packet["head_sha"], checks)
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
        rc, out, err = run_agent_v1(packet, packet["head_sha"], checks)
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
        rc, out, err = run_agent_v1(packet, packet["head_sha"], green_checks(names))
        self.assertEqual(rc, 0, err)
        new_doc = json.loads(out)
        # Simulated old reader: knows only the original 14 fields.
        old_view = {k: new_doc[k] for k in PACKET_FIELDS_14}
        self.assertEqual(old_view, packet)
        # And the additive block carries exactly the 8 specified fields.
        self.assertEqual(
            sorted(new_doc["agent_review"].keys()), sorted(AGENT_FIELDS_8))


class D1PinnedTableTest(unittest.TestCase):
    def test_t0_full_per_repo_table(self):
        policy = load_policy()
        self.assertEqual(policy["checks"], EXPECTED_PINNED_CHECKS)

    def test_t0_avc_stays_empty(self):
        policy = load_policy()
        self.assertEqual(
            policy["checks"]["autonomous-venture-company"], [])


class C3ApprovalBindingTest(unittest.TestCase):
    def _green(self, packet):
        policy = load_policy()
        return green_checks(policy["checks"][packet["repo"]])

    def test_t4_push_after_approval_is_blocked(self):
        packet = load_fixture()
        stale = make_approval(submitted_at="2026-09-10T07:00:00Z")
        binding = make_binding(reviews=[stale])
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], self._green(packet),
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("PUSH_AFTER_REVIEW", agent["reason_codes"])

    def test_t4_approval_after_push_stays_mergeable(self):
        packet = load_fixture()
        fresh = make_approval(submitted_at="2026-09-10T09:00:00Z")
        binding = make_binding(reviews=[fresh])
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], self._green(packet),
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "MERGEABLE")
        self.assertEqual(agent["reason_codes"], [])

    def test_t4_unresolved_conversations_blocked(self):
        packet = load_fixture()
        binding = make_binding(unresolved=2)
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], self._green(packet),
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("UNRESOLVED_CONVERSATIONS", agent["reason_codes"])

    def test_t4_codeowners_unmatched_blocked(self):
        packet = load_fixture()
        binding = make_binding(codeowners=False)
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], self._green(packet),
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("CODEOWNERS_UNMATCHED", agent["reason_codes"])

    def test_t4_approval_with_unknown_push_time_blocked(self):
        packet = load_fixture()
        binding = make_binding(pushed_at=None,
                               reviews=[make_approval()])
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], self._green(packet),
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("REVIEW_BINDING_UNKNOWN", agent["reason_codes"])


class T6AvcNoProtectionTest(unittest.TestCase):
    def test_t6_avc_without_override_is_blocked(self):
        packet = json.loads(AVC_FIXTURE.read_text(encoding="utf-8"))
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], {"checks": []},
            binding=green_binding())
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("NO_CI_PROTECTION", agent["reason_codes"])

    def test_t6_avc_with_owner_override_is_mergeable(self):
        packet = json.loads(AVC_FIXTURE.read_text(encoding="utf-8"))
        binding = make_binding(labels=[OVERRIDE_LABEL])
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], {"checks": []},
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "MERGEABLE")
        self.assertEqual(agent["reason_codes"], [])


class C4SeamChecksTest(unittest.TestCase):
    def _green_tg(self):
        packet = load_fixture()
        policy = load_policy()
        return packet, green_checks(policy["checks"][packet["repo"]])

    def _verdict(self, seams, now=NOW, packet=None, checks=None):
        packet, checks = (packet, checks) if packet else self._green_tg()
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], checks, binding=green_binding(),
            seams=seams, now=now)
        self.assertEqual(rc, 0, err)
        return json.loads(out)["agent_review"]

    def test_t7_resolved_ledger_ids_pass(self):
        seams = make_seams(cited_ids=["CON-001", "RET-007"],
                           ledger={"CON-001": {}, "RET-007": {}})
        agent = self._verdict(seams)
        self.assertEqual(agent["verdict"], "MERGEABLE")

    def test_t7_unresolved_ledger_id_blocked(self):
        seams = make_seams(cited_ids=["CON-999"], ledger={})
        agent = self._verdict(seams)
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_UNRESOLVED_ID", agent["reason_codes"])

    def test_t7_unknown_id_shape_blocked(self):
        seams = make_seams(cited_ids=["BOGUS-1"], ledger={"BOGUS-1": {}})
        agent = self._verdict(seams)
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_UNKNOWN_ID", agent["reason_codes"])

    def test_t7_genesis_binding_error_blocked(self):
        rec = good_record(genesis={"subject": "s", "purpose": "p"})
        agent = self._verdict(make_seams(records=[rec]))
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_GENESIS_BINDING_ERROR", agent["reason_codes"])

    def test_t7_expiry_at_cutoff_denies(self):
        # At-or-past cutoff denies (>=, never >): expiry == now BLOCKED.
        rec = good_record(expires_at=NOW)
        agent = self._verdict(make_seams(records=[rec]))
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_EXPIRED", agent["reason_codes"])

    def test_t7_future_expiry_passes(self):
        rec = good_record(expires_at="2026-09-11T00:00:00Z")
        agent = self._verdict(make_seams(records=[rec]))
        self.assertEqual(agent["verdict"], "MERGEABLE")

    def test_t7_incomplete_identity_blocked(self):
        rec = good_record(identity={"ids": ["id-1"]})
        agent = self._verdict(make_seams(records=[rec]))
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_IDENTITY_INCOMPLETE", agent["reason_codes"])

    def test_t7_bad_evidence_shape_blocked(self):
        for bad in ["evidence:/no-layer", "evidence:", "not-evidence",
                    "evidence:layer/"]:
            rec = good_record(evidence=bad)
            agent = self._verdict(make_seams(records=[rec]))
            self.assertEqual(agent["verdict"], "BLOCKED", bad)
            self.assertIn("SEAM_EVIDENCE_SHAPE_ERROR",
                          agent["reason_codes"], bad)

    def test_t7_contract_pin_mismatch_blocked(self):
        seams = make_seams(
            contract_pins={"platform-event-ref": "0.2",
                           "golden-mission": "0.1",
                           "voice-interaction": "0.1",
                           "promotion-gates": "0.1"})
        agent = self._verdict(seams)
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_CONTRACT_PIN_MISMATCH", agent["reason_codes"])

    def test_t7_matching_contract_pins_pass(self):
        seams = make_seams(
            contract_pins={"platform-event-ref": "0.1",
                           "golden-mission": "0.1",
                           "voice-interaction": "0.1",
                           "promotion-gates": "0.1"})
        agent = self._verdict(seams)
        self.assertEqual(agent["verdict"], "MERGEABLE")

    def test_t7_avc_new_identifiers_banned(self):
        packet = json.loads(AVC_FIXTURE.read_text(encoding="utf-8"))
        binding = make_binding(labels=[OVERRIDE_LABEL])
        seams = make_seams(new_identifiers=["NEW-THING-1"])
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], {"checks": []}, binding=binding,
            seams=seams)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_NEW_IDENTIFIER_BANNED", agent["reason_codes"])

    def test_t7_memory_as_authority_blocked(self):
        seams = make_seams(
            memory_authority_claims=["memory says CON-001 is valid"])
        agent = self._verdict(seams)
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("SEAM_MEMORY_AUTHORITY", agent["reason_codes"])


class EmitFileTest(unittest.TestCase):
    def test_t8_emit_file_matches_stdout(self):
        import tempfile
        packet = json.loads(AIE_FIXTURE.read_text(encoding="utf-8"))
        policy = load_policy()
        checks = green_checks(policy["checks"][packet["repo"]])
        with tempfile.TemporaryDirectory() as tmp:
            emit_dir = str(Path(tmp) / "evidence")
            rc, out, err, out_dir, emitted = run_agent(
                packet, packet["head_sha"], checks,
                binding=green_binding(), emit_dir=emit_dir)
            self.assertEqual(rc, 0, err)
            expected = "%s-%d-%s.json" % (
                packet["repo"], packet["number"], packet["head_sha"][:7])
            self.assertEqual(emitted, [expected])
            on_disk = json.loads(
                (out_dir / expected).read_text(encoding="utf-8"))
            self.assertEqual(on_disk, json.loads(out))

    def test_t8_no_emit_dir_writes_nothing(self):
        packet = load_fixture()
        policy = load_policy()
        checks = green_checks(policy["checks"][packet["repo"]])
        rc, out, err, _out_dir, emitted = run_agent(
            packet, packet["head_sha"], checks)
        self.assertEqual(rc, 0, err)
        self.assertEqual(emitted, [])


class FixtureReplayTest(unittest.TestCase):
    def test_t9_aie70_pinned_green_is_mergeable(self):
        packet = json.loads(AIE_FIXTURE.read_text(encoding="utf-8"))
        policy = load_policy()
        names = policy["checks"][packet["repo"]]
        live = {c["name"]: c for c in packet["checks"]}
        checks = {"checks": [live[n] for n in names]}
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], checks, binding=green_binding())
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "MERGEABLE")
        self.assertEqual(agent["reason_codes"], [])

    def test_t9_avc1021_replay_is_blocked_no_protection(self):
        packet = json.loads(AVC_FIXTURE.read_text(encoding="utf-8"))
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], {"checks": packet["checks"]},
            binding=green_binding())
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("NO_CI_PROTECTION", agent["reason_codes"])


class CommentOnlyGuardTest(unittest.TestCase):
    def test_agent_posts_nothing(self):
        action = ACTION.read_text(encoding="utf-8")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for text, name in ((action, "action.yml"),
                           (workflow, "agent-review.yml")):
            self.assertNotRegex(text, r"--approve",
                                "%s must never approve" % name)
            self.assertNotRegex(text, r"gh\s+pr\s+review\b",
                                "%s must never write reviews" % name)
            self.assertNotRegex(text, r"--method\s+POST\b",
                                "%s must not POST via gh api" % name)
        self.assertNotRegex(workflow, r"(?m)^\s+(contents|checks|"
                            r"pull-requests|issues|statuses|actions)"
                            r"\s*:\s*write\b",
                            "workflow permissions must stay read-only")


class T10SentinelBrandTest(unittest.TestCase):
    def test_t10_default_agent_name_is_sentinel_gate(self):
        packet = json.loads(FIXTURE.read_text(encoding="utf-8"))
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        pinned = policy["checks"][packet["repo"]]
        checks = {"checks": [
            {"name": n, "status": "COMPLETED", "conclusion": "SUCCESS"}
            for n in pinned]}
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = Path(tmp) / "packet.json"
            checks_path = Path(tmp) / "checks.json"
            packet_path.write_text(json.dumps(packet), encoding="utf-8")
            checks_path.write_text(json.dumps(checks), encoding="utf-8")
            cmd = [sys.executable, str(AGENT),
                   "--packet", str(packet_path),
                   "--current-head", packet["head_sha"],
                   "--checks", str(checks_path),
                   "--policy", str(POLICY)]
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        agent = json.loads(proc.stdout)["agent_review"]
        self.assertEqual(agent["name"], "sentinel-gate")


class T9Slice3WorkflowTest(unittest.TestCase):
    def test_t9_merge_group_trigger_present(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("merge_group:", workflow)

    def test_t9_push_audit_job_present_and_gated(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        script = (ROOT / "scripts" / "agent_review.py").read_text(
            encoding="utf-8")
        self.assertIn("push_audit:", workflow)
        self.assertIn("--audit-push", workflow)
        self.assertIn("NON_PR_HEAD", script)

    def test_t9_review_job_skips_push_events(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("github.event_name != 'push'", workflow)


class T7OverrideLabelRenameTest(unittest.TestCase):
    def test_t7_new_label_passes_avc(self):
        packet = json.loads(AVC_FIXTURE.read_text(encoding="utf-8"))
        binding = make_binding(labels=["OWNER_OVERRIDE_ACCEPT_RISK"])
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], {"checks": []},
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "MERGEABLE")
        self.assertEqual(agent["reason_codes"], [])

    def test_t7_old_label_no_longer_overrides(self):
        packet = json.loads(AVC_FIXTURE.read_text(encoding="utf-8"))
        binding = make_binding(labels=["owner-override"])
        rc, out, err, _d, _e = run_agent(
            packet, packet["head_sha"], {"checks": []},
            binding=binding)
        self.assertEqual(rc, 0, err)
        agent = json.loads(out)["agent_review"]
        self.assertEqual(agent["verdict"], "BLOCKED")
        self.assertIn("NO_CI_PROTECTION", agent["reason_codes"])


class T8PushAuditTest(unittest.TestCase):
    def test_t8_merged_pr_head_passes(self):
        rc, out, err = run_audit(
            [{"number": 1, "state": "closed",
              "merged_at": "2026-09-10T12:00:00Z"}])
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out)["reasons"], [])

    def test_t8_no_associated_pr_fails(self):
        rc, out, err = run_audit([])
        self.assertEqual(rc, 1)
        self.assertIn("NON_PR_HEAD", json.loads(out)["reasons"])

    def test_t8_closed_unmerged_fails(self):
        rc, out, err = run_audit(
            [{"number": 2, "state": "closed", "merged_at": None}])
        self.assertEqual(rc, 1)
        self.assertIn("NON_PR_HEAD", json.loads(out)["reasons"])

    def test_t8_open_pr_fails(self):
        rc, out, err = run_audit(
            [{"number": 3, "state": "open", "merged_at": None}])
        self.assertEqual(rc, 1)
        self.assertIn("NON_PR_HEAD", json.loads(out)["reasons"])


if __name__ == "__main__":
    unittest.main()
