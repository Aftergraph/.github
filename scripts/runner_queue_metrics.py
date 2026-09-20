#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

DEFAULT_REPOS = [
    "Aftergraph/.github",
    "Aftergraph/rendetalje",
    "Aftergraph/aie",
    "Aftergraph/works-execution",
    "Aftergraph/trust-gateway",
]

def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    xs = sorted(values)
    if len(xs) == 1:
        return xs[0]
    rank = (len(xs) - 1) * p
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return xs[lo]
    return xs[lo] + (xs[hi] - xs[lo]) * (rank - lo)

def gh_json(path: str) -> Any:
    proc = subprocess.run(
        ["gh", "api", "--paginate", path],
        check=True,
        text=True,
        capture_output=True,
        env=os.environ.copy(),
    )
    chunks = [chunk for chunk in proc.stdout.strip().split("\n") if chunk.strip()]
    if len(chunks) == 1:
        return json.loads(chunks[0])
    return [json.loads(chunk) for chunk in chunks]

def collect(repo: str, per_page: int) -> list[dict[str, Any]]:
    runs = gh_json(f"/repos/{repo}/actions/runs?per_page={per_page}")
    workflow_runs = runs.get("workflow_runs", []) if isinstance(runs, dict) else []
    samples: list[dict[str, Any]] = []

    for run in workflow_runs:
        run_id = run["id"]
        jobs = gh_json(f"/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")
        for job in jobs.get("jobs", []):
            created = parse_ts(run.get("created_at"))
            started = parse_ts(job.get("started_at"))
            completed = parse_ts(job.get("completed_at"))
            if not created or not started:
                continue
            queue_s = max(0.0, (started - created).total_seconds())
            duration_s = None if not completed else max(0.0, (completed - started).total_seconds())
            samples.append(
                {
                    "repo": repo,
                    "run_id": run_id,
                    "workflow": run.get("name"),
                    "head_sha": run.get("head_sha"),
                    "job": job.get("name"),
                    "runner_name": job.get("runner_name"),
                    "labels": job.get("labels") or [],
                    "queue_seconds": queue_s,
                    "duration_seconds": duration_s,
                    "status": job.get("status"),
                    "conclusion": job.get("conclusion"),
                    "created_at": run.get("created_at"),
                    "started_at": job.get("started_at"),
                    "completed_at": job.get("completed_at"),
                }
            )
    return samples

def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    queue = [float(s["queue_seconds"]) for s in samples]
    duration = [float(s["duration_seconds"]) for s in samples if s["duration_seconds"] is not None]
    cancelled = [s for s in samples if s["conclusion"] == "cancelled"]
    failed = [s for s in samples if s["conclusion"] == "failure"]
    skipped = [s for s in samples if s["conclusion"] == "skipped"]
    runners: dict[str, int] = {}
    for s in samples:
        name = s.get("runner_name") or "unassigned"
        runners[name] = runners.get(name, 0) + 1

    return {
        "schema": "aftergraph.runner-queue-metrics/1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample_count": len(samples),
        "queue_seconds": {
            "p50": percentile(queue, 0.50),
            "p95": percentile(queue, 0.95),
            "max": max(queue) if queue else None,
            "mean": statistics.mean(queue) if queue else None,
        },
        "duration_seconds": {
            "p50": percentile(duration, 0.50),
            "p95": percentile(duration, 0.95),
            "max": max(duration) if duration else None,
        },
        "outcomes": {
            "cancelled": len(cancelled),
            "failure": len(failed),
            "skipped": len(skipped),
            "cancelled_ratio": (len(cancelled) / len(samples)) if samples else 0.0,
        },
        "runner_assignment_counts": dict(sorted(runners.items(), key=lambda item: (-item[1], item[0]))),
    }

def recommendation(summary: dict[str, Any], target_p95: float) -> dict[str, Any]:
    p95 = summary["queue_seconds"]["p95"]
    cancelled_ratio = summary["outcomes"]["cancelled_ratio"]
    if p95 is None:
        action = "insufficient_samples"
    elif p95 <= target_p95 and cancelled_ratio == 0:
        action = "hold_capacity"
    elif p95 <= target_p95 * 2:
        action = "add_or_free_one_warm_lane"
    else:
        action = "scale_warm_pool_or_move_heavy_work_to_proof_pool"
    return {
        "target_queue_p95_seconds": target_p95,
        "observed_queue_p95_seconds": p95,
        "cancelled_ratio": cancelled_ratio,
        "action": action,
        "note": "Recommendation is capacity guidance only; it grants no execution authority.",
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append", dest="repos")
    parser.add_argument("--per-page", type=int, default=30)
    parser.add_argument("--target-p95-seconds", type=float, default=15.0)
    parser.add_argument("--out")
    args = parser.parse_args()

    repos = args.repos or DEFAULT_REPOS
    all_samples: list[dict[str, Any]] = []
    for repo in repos:
        all_samples.extend(collect(repo, args.per_page))

    result = {
        "summary": summarize(all_samples),
        "recommendation": None,
        "samples": all_samples,
    }
    result["recommendation"] = recommendation(result["summary"], args.target_p95_seconds)

    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload + "\n")
    print(payload)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
