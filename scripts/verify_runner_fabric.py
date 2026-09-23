#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "execution" / "runner-fabric-v1.json"
POLYREPO = ROOT / ".github" / "workflows" / "polyrepo-integration-gate.yml"
DOCTOR = ROOT / "scripts" / "doctor_runner_fabric_linux.sh"
MAINTENANCE = ROOT / "scripts" / "maintain_runner_fabric_linux.sh"

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
    freshness = queue.get("mid_run_freshness", {})
    if freshness.get("required_for_long_running_pr_jobs") is not True:
        errors.append("mid-run freshness invariant missing")
    if freshness.get("obsolete_head_behavior") != "neutral_skip_remaining_expensive_work":
        errors.append("obsolete-head neutral skip policy missing")

    host_health = policy.get("host_health", {})
    tmpfs = host_health.get("tmpfs", {})
    if tmpfs.get("path") != "/tmp":
        errors.append("runner tmpfs health path must be /tmp")
    if tmpfs.get("max_used_percent") != 85:
        errors.append("runner tmpfs max-used threshold drifted")
    if tmpfs.get("unhealthy_behavior") != "infrastructure_unavailable_not_code_failure":
        errors.append("runner tmpfs failure classification missing")
    listener_maintenance = host_health.get("listener_maintenance", {})
    if listener_maintenance.get("recycle_only_when_idle") is not True:
        errors.append("idle-only listener recycle policy missing")
    if listener_maintenance.get("require_no_runner_worker_child") is not True:
        errors.append("active Runner.Worker guard missing from policy")

    execution = policy.get("execution", {})
    if execution.get("one_runner_acquisition_per_gate") is not True:
        errors.append("single-acquisition invariant missing")
    if execution.get("exact_sha_receipt_required") is not True:
        errors.append("exact-SHA receipt invariant missing")

    workflow = POLYREPO.read_text(encoding="utf-8")
    required = [
        "runner_label:",
        "runs-on: ${{ inputs.runner_label }}",
        "default: 'ubuntu-latest'",
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

    rollout = policy.get("rollout", {})
    if rollout.get("organization_visible_self_hosted_pool_proven") is not False:
        errors.append("bootstrap policy must not claim org-visible self-hosted capacity before activation evidence")
    if rollout.get("default_central_runner") != "ubuntu-latest":
        errors.append("bootstrap central runner must remain known-good until activation")

    doctor = DOCTOR.read_text(encoding="utf-8")
    doctor_required = [
        "AFTERGRAPH_RUNNER_VERIFY_GITHUB",
        "/orgs/Aftergraph/actions/runners",
        "GITHUB_ORG_VISIBLE_READY=",
        "RUNNER_FABRIC_DOCTOR=PASS",
        "RUNNER_TMPFS_HEALTH=PASS",
        "RUNNER_LISTENER_DELETED_MEMFD_MAPPINGS=",
    ]
    for marker in doctor_required:
        if marker not in doctor:
            errors.append(f"runner doctor missing: {marker}")

    maintenance = MAINTENANCE.read_text(encoding="utf-8")
    maintenance_required = [
        "recycle-idle",
        "root_required",
        "active_worker_children",
        "listener_too_young",
        "no_deleted_memfd_mapping",
        'systemctl restart "$unit"',
        "RUNNER_FABRIC_MAINTENANCE=PASS",
    ]
    for marker in maintenance_required:
        if marker not in maintenance:
            errors.append(f"runner maintenance missing: {marker}")

    forbidden = [
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
