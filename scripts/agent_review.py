#!/usr/bin/env python3
"""Slice-1 code-review agent (READ-ONLY).

Implements:
  C1 delta-vs-reviewed-head: current head_sha vs reviewed/packet head_sha.
     Any mismatch => verdict BLOCKED + reason DELTA_MISMATCH.
  C2 pinned-checks gate: policies/pinned-checks.json per-repo named checks.
     Each pinned name must be present with status COMPLETED and conclusion
     SUCCESS. Missing => PINNED_CHECK_MISSING, not completed =>
     PINNED_CHECK_PENDING, completed non-success => PINNED_CHECK_FAILED.
     Any of these => verdict BLOCKED. Unknown repos fail closed with
     POLICY_UNKNOWN_REPO.

Reads the reviewed packet, live current head SHA, and live checks. Emits the
14-field review packet PLUS an additive `agent_review` block as JSON to
stdout only. Posts NOTHING: no comments, no statuses, no governance writes.
Exit 0 whenever a packet is emitted; non-zero only on tool errors.
Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

AGENT_BLOCK_FIELDS = (
    "name", "version", "run_id", "reviewed_head_sha", "current_head_sha",
    "delta_clean", "verdict", "reason_codes",
)


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


def check_delta(reviewed_head, current_head):
    """C1: True when the live head still equals the reviewed head."""
    return reviewed_head == current_head


def check_pinned_checks(repo, live_checks, policy):
    """C2: reason codes for the pinned-checks gate (empty => gate passes)."""
    reasons = []
    pinned = (policy.get("checks") or {}).get(repo)
    if pinned is None:
        return ["POLICY_UNKNOWN_REPO"]
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


def evaluate(packet, current_head, live_checks, policy, agent_meta):
    reviewed_head = packet["head_sha"]
    delta_clean = check_delta(reviewed_head, current_head)
    reasons = check_pinned_checks(packet["repo"], live_checks, policy)
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
    parser.add_argument("--agent-name", default="agent-review")
    parser.add_argument("--agent-version", default="0.1.0")
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

    out = evaluate(packet, args.current_head, checks_doc["checks"], policy,
                   {"name": args.agent_name, "version": args.agent_version,
                    "run_id": args.run_id})
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
