#!/usr/bin/env python3
"""Slice-2 code-review agent (READ-ONLY, COMMENT-ONLY permanently).

Implements:
  C1 delta-vs-reviewed-head: current head_sha vs reviewed/packet head_sha.
     Any mismatch => verdict BLOCKED + reason DELTA_MISMATCH.
  C2 pinned-checks gate: policies/pinned-checks.json per-repo named checks.
     Each pinned name must be present with status COMPLETED and conclusion
     SUCCESS. Missing => PINNED_CHECK_MISSING, not completed =>
     PINNED_CHECK_PENDING, completed non-success => PINNED_CHECK_FAILED.
     Any of these => verdict BLOCKED. Unknown repos fail closed with
     POLICY_UNKNOWN_REPO. Repos with an explicitly empty pin list (no CI,
     currently autonomous-venture-company) fail closed with NO_CI_PROTECTION
     unless the owner-override label is present in the binding input.
  C3 approval/binding (--binding JSON, optional): push-after-review
     invalidates verdict (an APPROVED review submitted before the head commit
     was pushed => PUSH_AFTER_REVIEW); unresolved review conversations =>
     UNRESOLVED_CONVERSATIONS; CODEOWNERS not matched =>
     CODEOWNERS_UNMATCHED; approvals that cannot be bound to a push time =>
     REVIEW_BINDING_UNKNOWN. Any of these => verdict BLOCKED. Absent
     binding file => C3 skipped (the scheduled workflow always provides it).
  C4 seam checks (--seams JSON + --seam-rules policy): every cited ledger ID
     must match a known shape (SEAM_UNKNOWN_ID) and resolve to a ledger
     entry (SEAM_UNRESOLVED_ID); genesis snapshots must carry
     subject/purpose/tenant (SEAM_GENESIS_BINDING_ERROR); identity must be
     complete (SEAM_IDENTITY_INCOMPLETE); evidence must match
     evidence:<layer>/<id> (SEAM_EVIDENCE_SHAPE_ERROR); expiry denies
     at-or-past cutoff (SEAM_EXPIRED); contract pins must match
     (SEAM_CONTRACT_PIN_MISMATCH); banned new identifiers
     (SEAM_NEW_IDENTIFIER_BANNED); memory-as-authority claims
     (SEAM_MEMORY_AUTHORITY). Any ERROR/UNKNOWN => verdict BLOCKED. Absent
     seams file => C4 skipped.

Reads the reviewed packet, live current head SHA, and live checks. Emits the
14-field review packet PLUS an additive `agent_review` block as JSON to
stdout (always) and, with --emit-dir, to
docs/evidence/agent-review/<repo>-<num>-<shortsha>.json style files.
Posts NOTHING: no comments, no approvals, no reviews writes, no statuses,
no governance writes. Exit 0 whenever a packet is emitted; non-zero only
on tool errors. Stdlib only.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

AGENT_BLOCK_FIELDS = (
    "name", "version", "run_id", "reviewed_head_sha", "current_head_sha",
    "delta_clean", "verdict", "reason_codes",
)

OVERRIDE_LABEL = "owner-override"

APPROVED_STATE = "APPROVED"


def fail(msg):
    print(f"agent_review: error: {msg}", file=sys.stderr)
    return 2


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        return exc


def parse_time(value):
    """Parse an ISO-8601 timestamp; return aware datetime or None."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        moment = datetime.fromisoformat(text)
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment


def utcnow():
    return datetime.now(timezone.utc)


def check_delta(reviewed_head, current_head):
    """C1: True when the live head still equals the reviewed head."""
    return reviewed_head == current_head


def check_pinned_checks(repo, live_checks, policy, labels=()):
    """C2: reason codes for the pinned-checks gate (empty => gate passes)."""
    reasons = []
    pinned = (policy.get("checks") or {}).get(repo)
    if pinned is None:
        return ["POLICY_UNKNOWN_REPO"]
    if len(pinned) == 0:
        # No CI on this repo: fail closed unless the owner explicitly
        # overrides with the owner-override label.
        if OVERRIDE_LABEL in (labels or ()):
            return []
        return ["NO_CI_PROTECTION"]
    by_name = {}
    for check in live_checks:
        if isinstance(check, dict) and "name" in check:
            by_name.setdefault(check["name"], check)
    for name in pinned:
        check = by_name.get(name)
        if check is None:
            reasons.append("PINNED_CHECK_MISSING")
            continue
        if check.get("status") != "COMPLETED":
            reasons.append("PINNED_CHECK_PENDING")
        elif check.get("conclusion") != "SUCCESS":
            reasons.append("PINNED_CHECK_FAILED")
    # De-duplicate while preserving policy order.
    seen = set()
    ordered = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            ordered.append(reason)
    return ordered


def check_binding(binding):
    """C3: reason codes for approval/binding (empty => gate passes)."""
    reasons = []
    if not isinstance(binding, dict):
        return ["REVIEW_BINDING_UNKNOWN"]
    unresolved = binding.get("unresolved_conversations", 0)
    if not isinstance(unresolved, int) or unresolved > 0:
        reasons.append("UNRESOLVED_CONVERSATIONS")
    if binding.get("codeowners_matched") is not True:
        reasons.append("CODEOWNERS_UNMATCHED")
    reviews = binding.get("reviews", [])
    if not isinstance(reviews, list):
        return reasons + ["REVIEW_BINDING_UNKNOWN"]
    approvals = [r for r in reviews
                 if isinstance(r, dict) and r.get("state") == APPROVED_STATE]
    if not approvals:
        return reasons
    pushed_at = parse_time(binding.get("head_commit_pushed_at"))
    if pushed_at is None:
        return reasons + ["REVIEW_BINDING_UNKNOWN"]
    for review in approvals:
        submitted_at = parse_time(review.get("submitted_at"))
        if submitted_at is None or submitted_at < pushed_at:
            reasons.append("PUSH_AFTER_REVIEW")
            break
    return reasons


def check_seams(repo, seams, rules, now):
    """C4: reason codes for seam checks (empty => gate passes).

    Fail closed: any malformed entry or unresolvable reference yields an
    ERROR/UNKNOWN reason, which always blocks.
    """
    reasons = []
    if not isinstance(seams, dict) or not isinstance(rules, dict):
        return ["SEAM_UNKNOWN"]
    try:
        patterns = [re.compile("^(" + p + ")$")
                    for p in rules.get("ledger_id_patterns", [])]
    except re.error:
        return ["SEAM_UNKNOWN"]
    ledger = seams.get("ledger", {})
    if not isinstance(ledger, dict):
        return ["SEAM_UNKNOWN"]
    cited = seams.get("cited_ids", [])
    if not isinstance(cited, list):
        return ["SEAM_UNKNOWN"]
    for cited_id in cited:
        if not isinstance(cited_id, str):
            reasons.append("SEAM_UNKNOWN_ID")
            continue
        if not any(p.match(cited_id) for p in patterns):
            reasons.append("SEAM_UNKNOWN_ID")
        elif cited_id not in ledger:
            reasons.append("SEAM_UNRESOLVED_ID")
    records = seams.get("records", [])
    if not isinstance(records, list):
        return reasons + ["SEAM_UNKNOWN"]
    try:
        evidence_re = re.compile(rules.get("evidence_pattern", r"(?!)"))
    except re.error:
        return reasons + ["SEAM_UNKNOWN"]
    genesis_fields = rules.get("genesis_required_fields", [])
    identity_fields = rules.get("identity_required_fields", [])
    for record in records:
        if not isinstance(record, dict):
            reasons.append("SEAM_UNKNOWN")
            continue
        genesis = record.get("genesis")
        if not isinstance(genesis, dict) or any(
                genesis.get(f) in (None, "") for f in genesis_fields):
            reasons.append("SEAM_GENESIS_BINDING_ERROR")
        identity = record.get("identity")
        if not isinstance(identity, dict):
            reasons.append("SEAM_IDENTITY_INCOMPLETE")
        else:
            for field in identity_fields:
                if field not in identity:
                    reasons.append("SEAM_IDENTITY_INCOMPLETE")
                    break
                # Lineage is null-or-state: the key must exist but null
                # is a legal value. Every other field must be non-empty,
                # and timestamps must be ISO-8601.
                if field == "lineage":
                    continue
                value = identity.get(field)
                if value in (None, "", []):
                    reasons.append("SEAM_IDENTITY_INCOMPLETE")
                    break
                if field == "timestamp" and parse_time(value) is None:
                    reasons.append("SEAM_IDENTITY_INCOMPLETE")
                    break
        evidence = record.get("evidence")
        if not isinstance(evidence, str) or not evidence_re.match(evidence):
            reasons.append("SEAM_EVIDENCE_SHAPE_ERROR")
        expires_at = record.get("expires_at")
        if expires_at is not None:
            cutoff = parse_time(expires_at)
            if cutoff is None:
                reasons.append("SEAM_UNKNOWN")
            elif now >= cutoff:
                reasons.append("SEAM_EXPIRED")
    pins = seams.get("contract_pins", {})
    required_pins = rules.get("contract_pins") or {}
    if not isinstance(pins, dict):
        reasons.append("SEAM_UNKNOWN")
    else:
        for name, version in pins.items():
            if name not in required_pins:
                reasons.append("SEAM_UNKNOWN")
                break
            if version != required_pins[name]:
                reasons.append("SEAM_CONTRACT_PIN_MISMATCH")
                break
    banned_repos = rules.get("no_new_identifiers_repos", [])
    new_ids = seams.get("new_identifiers", [])
    if not isinstance(new_ids, list):
        reasons.append("SEAM_UNKNOWN")
    elif new_ids and repo in banned_repos:
        reasons.append("SEAM_NEW_IDENTIFIER_BANNED")
    claims = seams.get("memory_authority_claims", [])
    if not isinstance(claims, list):
        reasons.append("SEAM_UNKNOWN")
    elif rules.get("memory_authority_deny") and len(claims) > 0:
        reasons.append("SEAM_MEMORY_AUTHORITY")
    seen = set()
    ordered = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            ordered.append(reason)
    return ordered


def evaluate(packet, current_head, live_checks, policy, agent_meta,
             binding=None, seams=None, seam_rules=None, now=None):
    reviewed_head = packet["head_sha"]
    delta_clean = check_delta(reviewed_head, current_head)
    labels = []
    if isinstance(binding, dict) and isinstance(
            binding.get("labels"), list):
        labels = binding["labels"]
    reasons = check_pinned_checks(packet["repo"], live_checks, policy,
                                  labels=labels)
    if binding is not None:
        reasons = reasons + check_binding(binding)
    if seams is not None:
        reasons = reasons + check_seams(packet["repo"], seams,
                                        seam_rules or {}, now or utcnow())
    if not delta_clean:
        reasons = ["DELTA_MISMATCH"] + reasons
    verdict = "MERGEABLE" if not reasons else "BLOCKED"
    out = dict(packet)
    out["agent_review"] = {
        "name": agent_meta["name"],
        "version": agent_meta["version"],
        "run_id": agent_meta["run_id"],
        "reviewed_head_sha": reviewed_head,
        "current_head_sha": current_head,
        "delta_clean": delta_clean,
        "verdict": verdict,
        "reason_codes": reasons,
    }
    return out


def emit_packet(doc, emit_dir):
    """Write the packet file; return the filename (raises on tool error)."""
    target = Path(emit_dir)
    target.mkdir(parents=True, exist_ok=True)
    name = "%s-%d-%s.json" % (
        doc["repo"], doc["number"], doc["head_sha"][:7])
    path = target / name
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")
    return name


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True,
                        help="Reviewed 14-field packet JSON file.")
    parser.add_argument("--current-head", required=True,
                        help="Live PR head SHA (40 lowercase hex).")
    parser.add_argument("--checks", required=True,
                        help='Live checks JSON file ({"checks": [...]}).')
    parser.add_argument("--policy", required=True,
                        help="Pinned-checks policy JSON file.")
    parser.add_argument("--binding", default=None,
                        help="Approval/binding JSON file for the C3 gate.")
    parser.add_argument("--seams", default=None,
                        help="Seam-evidence JSON file for the C4 gate.")
    parser.add_argument("--seam-rules", default=None,
                        help="Seam-rules policy JSON file (needs --seams).")
    parser.add_argument("--now", default=None,
                        help="Reference ISO-8601 time for expiry checks.")
    parser.add_argument("--emit-dir", default=None,
                        help="Directory for the per-PR packet file "
                             "(D5; stdout is always emitted too).")
    parser.add_argument("--agent-name", default="agent-review")
    parser.add_argument("--agent-version", default="0.2.0")
    parser.add_argument("--run-id", default="local")
    args = parser.parse_args(argv)

    if not SHA_RE.match(args.current_head):
        print("agent_review: error: --current-head must be 40 lowercase hex",
              file=sys.stderr)
        return 2

    packet = load_json(args.packet)
    if packet is None:
        print(f"agent_review: error: packet file not found: {args.packet}",
              file=sys.stderr)
        return 2
    if isinstance(packet, Exception):
        print(f"agent_review: error: packet file is not valid JSON: {packet}",
              file=sys.stderr)
        return 2
    if not isinstance(packet, dict) or not SHA_RE.match(
            str(packet.get("head_sha", ""))):
        print("agent_review: error: packet must be an object with a valid "
              "head_sha", file=sys.stderr)
        return 2
    if "repo" not in packet:
        print("agent_review: error: packet is missing 'repo'",
              file=sys.stderr)
        return 2

    checks_doc = load_json(args.checks)
    if checks_doc is None:
        print(f"agent_review: error: checks file not found: {args.checks}",
              file=sys.stderr)
        return 2
    if isinstance(checks_doc, Exception) or not isinstance(checks_doc, dict) \
            or not isinstance(checks_doc.get("checks"), list):
        print('agent_review: error: checks file must be JSON like '
              '{"checks": [...]}', file=sys.stderr)
        return 2

    policy = load_json(args.policy)
    if policy is None:
        print(f"agent_review: error: policy file not found: {args.policy}",
              file=sys.stderr)
        return 2
    if isinstance(policy, Exception) or not isinstance(policy, dict):
        print("agent_review: error: policy file is not a valid JSON object",
              file=sys.stderr)
        return 2

    binding = None
    if args.binding is not None:
        binding = load_json(args.binding)
        if binding is None:
            print("agent_review: error: binding file not found: "
                  f"{args.binding}", file=sys.stderr)
            return 2
        if isinstance(binding, Exception) or not isinstance(binding, dict):
            print("agent_review: error: binding file is not a valid "
                  "JSON object", file=sys.stderr)
            return 2

    seams = None
    seam_rules = None
    if args.seams is not None:
        if args.seam_rules is None:
            print("agent_review: error: --seams needs --seam-rules",
                  file=sys.stderr)
            return 2
        seams = load_json(args.seams)
        if seams is None:
            print("agent_review: error: seams file not found: "
                  f"{args.seams}", file=sys.stderr)
            return 2
        if isinstance(seams, Exception) or not isinstance(seams, dict):
            print("agent_review: error: seams file is not a valid "
                  "JSON object", file=sys.stderr)
            return 2
        seam_rules = load_json(args.seam_rules)
        if seam_rules is None:
            print("agent_review: error: seam-rules file not found: "
                  f"{args.seam_rules}", file=sys.stderr)
            return 2
        if isinstance(seam_rules, Exception) or not isinstance(
                seam_rules, dict):
            print("agent_review: error: seam-rules file is not a valid "
                  "JSON object", file=sys.stderr)
            return 2

    now = utcnow()
    if args.now is not None:
        now = parse_time(args.now)
        if now is None:
            print("agent_review: error: --now must be ISO-8601",
                  file=sys.stderr)
            return 2

    out = evaluate(packet, args.current_head, checks_doc["checks"], policy,
                   {"name": args.agent_name, "version": args.agent_version,
                    "run_id": args.run_id},
                   binding=binding, seams=seams, seam_rules=seam_rules,
                   now=now)
    text = json.dumps(out, indent=2, sort_keys=True)
    print(text)
    if args.emit_dir is not None:
        try:
            emit_packet(out, args.emit_dir)
        except OSError as exc:
            print(f"agent_review: error: cannot write emit file: {exc}",
                  file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
