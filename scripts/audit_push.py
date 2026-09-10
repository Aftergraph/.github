#!/usr/bin/env python3
"""Direct-to-main push audit (slice 3, detective, emit-only).

Checks whether a main-branch head commit is associated with a pull request
(via the GitHub `commits/<sha>/pulls` API output saved to a file). A head
with at least one associated PR passes; a head with none is a direct-to-main
push: the script appends a finding to the packet stream (JSON on stdout) and
exits non-zero so the push-audit job FAILS VISIBLY.

Detective, non-preventive: the push already landed; this job flags it, it
does not prevent it. Forced pushes by an admin remain possible; they are
flagged, not prevented (see docs/agent-review.md residue risks).

Posts NOTHING: no comments, no statuses, no writes. Stdlib only.
Exit 0 on AUDIT_PASS, 1 on AUDIT_FAIL, 2 on tool errors.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        return exc


def extract_prs(doc):
    """Normalize gh `commits/<sha>/pulls` output to a PR list."""
    if isinstance(doc, list):
        return doc
    if isinstance(doc, dict):
        for key in ("prs", "pulls", "associated_prs", "pull_requests"):
            if isinstance(doc.get(key), list):
                return doc[key]
    return None


def audit(head_sha, prs):
    associated = len(prs) > 0
    if associated:
        numbers = sorted({
            p.get("number") for p in prs
            if isinstance(p, dict) and isinstance(p.get("number"), int)})
        if numbers:
            detail = "associated with PR #{}".format(
                ", #".join(str(n) for n in numbers))
        else:
            detail = "associated with {} pull request(s)".format(len(prs))
        finding = ("main head {} is {} (merged via PR; "
                   "detective audit PASS).".format(head_sha, detail))
        return {"head_sha": head_sha, "pr_associated": True,
                "verdict": "AUDIT_PASS", "finding": finding}, 0
    finding = ("direct-to-main push: main head {} has no associated pull "
               "request (detective audit FAIL; non-preventive — the push "
               "already landed; investigate and revert if "
               "unauthorized).".format(head_sha))
    return {"head_sha": head_sha, "pr_associated": False,
            "verdict": "AUDIT_FAIL", "finding": finding}, 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--head-sha", required=True,
                        help="Main-branch head SHA (40 lowercase hex).")
    parser.add_argument("--associated-prs", required=True,
                        help="JSON file with gh `commits/<sha>/pulls` output "
                             "(a JSON list, or an object with a prs/pulls "
                             "list).")
    parser.add_argument("--run-id", default="local")
    args = parser.parse_args(argv)

    if not SHA_RE.match(args.head_sha):
        print("audit_push: error: --head-sha must be 40 lowercase hex",
              file=sys.stderr)
        return 2

    doc = load_json(args.associated_prs)
    if doc is None:
        print("audit_push: error: associated-prs file not found: {}".format(
            args.associated_prs), file=sys.stderr)
        return 2
    if isinstance(doc, Exception):
        print("audit_push: error: associated-prs file is not valid JSON: "
              "{}".format(doc), file=sys.stderr)
        return 2
    prs = extract_prs(doc)
    if prs is None:
        print("audit_push: error: associated-prs file must be a JSON list "
              "or an object with a prs/pulls list", file=sys.stderr)
        return 2

    out, code = audit(args.head_sha, prs)
    out["run_id"] = args.run_id
    print(json.dumps(out, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
