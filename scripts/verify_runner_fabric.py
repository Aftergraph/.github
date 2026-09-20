#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "execution" / "runner-fabric-v1.json"
POLYREPO = ROOT / ".github" / "workflows" / "polyrepo-integration-gate.yml"

def verify() -> list[str]:
    errors: list[str] = []
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy.get("$id") != "aftergraph.runner-fabric/1.0":
        errors.append("wrong runner fabric id")

    queue = policy.get("queue", {})
    if queue.get("desired_behavior") != "latest_exact_sha_wins_before_execution":
        errors.append("latest-SHA coalescing policy missing")
    if queue.get("infrastructure_unavailable") != "neutral_or_pending_not_code_failure":
        errors.append("infrastructure/code-failure separation missing")

    execution = policy.get("execution", {})
    if execution.get("one_runner_acquisition_per_gate") is not True:
        errors.append("single-acquisition invariant missing")
    if execution.get("exact_sha_receipt_required") is not True:
        errors.append("exact-SHA receipt invariant missing")

    workflow = POLYREPO.read_text(encoding="utf-8")
    required = [
        "runs-on: [self-hosted, Linux, X64, aftergraph-ci]",
        "actions/checkout@v7",
        "actions/setup-node@v7",
        "actions/setup-python@v7",
        "actions/setup-go@v7",
        "persist-credentials: false",
        "governance_ref:",
        "aie_ref:",
        "works_ref:",
        "isr_ref:",
        "EXACT_HEAD=",
    ]
    for marker in required:
        if marker not in workflow:
            errors.append(f"polyrepo workflow missing: {marker}")

    forbidden = [
        "runs-on: ubuntu-latest",
        "cancel-in-progress: true",
    ]
    for marker in forbidden:
        if marker in workflow:
            errors.append(f"polyrepo workflow forbids: {marker}")

    return errors

def main() -> int:
    errors = verify()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("Runner Fabric v1 contract PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
