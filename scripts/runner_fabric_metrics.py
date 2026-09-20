#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import statistics
import subprocess
from typing import Any

DEFAULT_REPOS = (
    "Aftergraph/.github",
    "Aftergraph/aie",
    "Aftergraph/works-execution",
    "Aftergraph/trust-gateway",
    "Aftergraph/rendetalje",
)

def parse_time(value: str | None) -> dt.datetime | None:
    if not value:
        return None
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))

def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    lo = int(rank)
    hi = min(lo + 1, len(ordered) - 1)
    frac = rank - lo
    return ordered[lo] * (1 - frac) + ordered[hi] * frac

def summarize(
    runs: list[dict[str, Any]],
    jobs_by_run: dict[int, list[dict[str, Any]]],
    queue_target_seconds: float = 15.0,
) -> dict[str, Any]:
    queue_seconds: list[float] = []
    job_runtime_seconds: list[float] = []
    runners: set[str] = set()
    completed = 0
    cancelled = 0

    for run in runs:
        if run.get("status") == "completed":
            completed += 1
        if run.get("conclusion") == "cancelled":
            cancelled += 1

        created = parse_time(run.get("created_at"))
        jobs = jobs_by_run.get(int(run["id"]), [])
        starts = [parse_time(job.get("started_at")) for job in jobs]
        starts = [value for value in starts if value is not None]
        if created is not None and starts:
            queue_seconds.append(max(0.0, (min(starts) - created).total_seconds()))

        for job in jobs:
            name = job.get("runner_name")
            if isinstance(name, str) and name:
                runners.add(name)
            started = parse_time(job.get("started_at"))
            finished = parse_time(job.get("completed_at"))
            if started is not None and finished is not None:
                job_runtime_seconds.append(max(0.0, (finished - started).total_seconds()))

    p50 = percentile(queue_seconds, 0.50)
    p95 = percentile(queue_seconds, 0.95)
    runtime_p95 = percentile(job_runtime_seconds, 0.95)
    cancellation_rate = cancelled / len(runs) if runs else 0.0
    pressure = p95 is not None and p95 > queue_target_seconds

    return {
        "run_samples": len(runs),
        "completed_samples": completed,
        "job_samples": sum(len(v) for v in jobs_by_run.values()),
        "queue_seconds": {
            "p50": round(p50, 2) if p50 is not None else None,
            "p95": round(p95, 2) if p95 is not None else None,
            "target_p95": queue_target_seconds,
        },
        "job_runtime_seconds": {
            "p95": round(runtime_p95, 2) if runtime_p95 is not None else None,
        },
        "cancelled_runs": cancelled,
        "cancellation_rate": round(cancellation_rate, 4),
        "observed_runners": sorted(runners),
        "capacity_signal": "pressure" if pressure else "within_target",
        "scale_hint": "add_or_rebalance_warm_capacity" if pressure else "hold_and_measure",
    }

def gh_json(path: str) -> Any:
    proc = subprocess.run(
        ["gh", "api", path],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh_api_failed:{path}:{proc.stderr.strip()[:300]}")
    return json.loads(proc.stdout)

def collect_repo(repo: str, limit: int) -> dict[str, Any]:
    payload = gh_json(f"/repos/{repo}/actions/runs?per_page={limit}")
    runs = list(payload.get("workflow_runs", []))[:limit]
    jobs_by_run: dict[int, list[dict[str, Any]]] = {}
    for run in runs:
        run_id = int(run["id"])
        jobs_payload = gh_json(f"/repos/{repo}/actions/runs/{run_id}/jobs?per_page=100")
        jobs_by_run[run_id] = list(jobs_payload.get("jobs", []))
    return summarize(runs, jobs_by_run)

def main() -> int:
    parser = argparse.ArgumentParser(description="Measure Aftergraph runner queue health.")
    parser.add_argument("repos", nargs="*", default=list(DEFAULT_REPOS))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.limit < 1 or args.limit > 100:
        raise SystemExit("--limit must be 1..100")

    result = {
        "schema": "aftergraph.runner-fabric.metrics/1.0",
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repositories": {repo: collect_repo(repo, args.limit) for repo in args.repos},
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for repo, summary in result["repositories"].items():
            q = summary["queue_seconds"]
            print(
                f"{repo}: queue p50={q['p50']}s p95={q['p95']}s "
                f"cancel_rate={summary['cancellation_rate']:.1%} "
                f"signal={summary['capacity_signal']} "
                f"runners={','.join(summary['observed_runners']) or '-'}"
            )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
