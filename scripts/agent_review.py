#!/usr/bin/env python3
"""Slice-3 (final) code-review agent (READ-ONLY, COMMENT-only, emit-only).

Implements:
  C1 delta-vs-reviewed-head: current head_sha vs reviewed/packet head_sha.
     Any mismatch => verdict BLOCKED + reason DELTA_MISMATCH.
  C2 pinned-checks gate: policies/pinned-checks.json per-repo named checks
     (full D1 pin set, all 8 repos). Each pinned name must be present with
     status COMPLETED and conclusion SUCCESS. Missing =>
     PINNED_CHECK_MISSING, not completed => PINNED_CHECK_PENDING,
     completed non-success => PINNED_CHECK_FAILED. Any of these => verdict
     BLOCKED. Unknown repos fail closed with POLICY_UNKNOWN_REPO.
  C3 private-repo mode (slice 3): a KNOWN repo with an EMPTY pin set
     (autonomous-venture-company: no CI) stays BLOCKED with reason
     EMPTY_PIN_SET unless the explicit owner-override label
     OWNER_OVERRIDE_ACCEPT_RISK is present on the PR. With the override
     (and a clean delta) the verdict is MERGEABLE with reason
     OWNER_OVERRIDE_ACCEPT_RISK recorded (explicit, never a silent pass).
     Delta mismatch still BLOCKED. The override never bypasses pinned-check
     failures on other repos.

Reads the reviewed packet, live current head SHA, live checks, and PR
labels. Emits the 14-field review packet PLUS an additive `agent_review`
block as JSON to stdout only. Posts NOTHING: no comments, no approvals,
no reviews writes, no statuses, no governance writes (COMMENT-only
permanently; this slice emits only).
Exit 0 whenever a packet is emitted; non-zero only on tool errors.
Stdlib only.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")

OWNER_OVERRIDE_LABEL = "OWNER_OVERRIDE_ACCEPT_RISK"
EMPTY_PIN_SET_REASON = "EMPTY_PIN_SET"

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


def parse_labels(value):
    """Parse --labels: comma-separated names or a JSON list string."""
    if value is None:
        return []
    text = value.strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("--labels JSON list could not be parsed")
        if not isinstance(parsed, list) or not all(
                isinstance(item, str) for item in parsed):
            raise ValueError("--labels JSON must be a list of strings")
        return [item.strip() for item in parsed if item.strip()]
    return [item.strip() for item in text.split(",") if item.strip()]


def load_labels_file(path):
    """Load PR labels from a JSON file (list or {"labels": [...]})."""
    doc = load_json(path)
    if doc is None:
        raise FileNotFoundError(f"labels file not found: {path}")
    if isinstance(doc, Exception):
        raise ValueError(f"labels file is not valid JSON: {doc}")
    if isinstance(doc, list):
        items = doc
    elif isinstance(doc, dict):
        items = None
        for key in ("labels", "pr_labels", "names"):
            if isinstance(doc.get(key), list):
                items = doc[key]
                break
        if items is None:
            raise ValueError(
                'labels file must be a JSON list or an object with a '
                '"labels" list')
    else:
        raise ValueError("labels file must be a JSON list or object")
    if not all(isinstance(item, str) for item in items):
        raise ValueError("labels file must contain only strings")
    # Accept both bare names and {"name": ...} label objects.
    cleaned = []
    for item in items:
        cleaned.append(item.strip())
    return [item for item in cleaned if item]


def check_pinned_checks(repo, live_checks, policy, labels=()):
    """C2+C3: reason codes for the pinned-checks / private-repo gate."""
    reasons = []
    pinned = (policy.get("checks") or {}).get(repo)
    if pinned is None:
        return ["POLICY_UNKNOWN_REPO"]
    if len(pinned) == 0:
        # C3 private-repo mode: empty pin set (AVC, no CI) never passes
        # silently. Explicit owner override only.
        if OWNER_OVERRIDE_LABEL in set(labels or ()):
            return [OWNER_OVERRIDE_LABEL]
        return [EMPTY_PIN_SET_REASON]
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


def evaluate(packet, current_head, live_checks, policy, agent_meta,
             labels=()):
    reviewed_head = packet["head_sha"]
    delta_clean = check_delta(reviewed_head, current_head)
    reasons = check_pinned_checks(packet["repo"], live_checks, policy,
                                  labels=labels)
    if not delta_clean:
        reasons = ["DELTA_MISMATCH"] + reasons
    if not reasons:
        verdict = "MERGEABLE"
    elif reasons == [OWNER_OVERRIDE_LABEL] and delta_clean:
        # Explicit owner-accepted risk on an empty pin set: mergeable but
        # recorded, never silent.
        verdict = "MERGEABLE"
    else:
        verdict = "BLOCKED"
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
    parser.add_argument("--labels", default=None,
                        help="PR labels: comma-separated or JSON list.")
    parser.add_argument("--labels-file", default=None,
                        help='PR labels JSON file (list or {"labels": [...]})')
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

    try:
        labels = parse_labels(args.labels)
    except ValueError as exc:
        print(f"agent_review: error: {exc}", file=sys.stderr)
        return 2
    if args.labels_file:
        try:
            labels += load_labels_file(args.labels_file)
        except (FileNotFoundError, ValueError) as exc:
            print(f"agent_review: error: {exc}", file=sys.stderr)
            return 2
    # De-duplicate labels preserving order.
    seen_labels = set()
    ordered_labels = []
    for label in labels:
        if label not in seen_labels:
            seen_labels.add(label)
            ordered_labels.append(label)

    out = evaluate(packet, args.current_head, checks_doc["checks"], policy,
                   {"name": args.agent_name, "version": args.agent_version,
                    "run_id": args.run_id}, labels=ordered_labels)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
