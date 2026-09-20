# Runner queue telemetry

Runner Fabric capacity decisions must be based on measured queue latency, not on
the number of configured runners alone.

`scripts/runner_queue_metrics.py` reads GitHub Actions run/job timestamps with
the GitHub CLI and produces:

- queue p50 / p95 / max;
- execution duration p50 / p95 / max;
- cancelled / failed / skipped counts;
- cancelled ratio;
- observed runner assignment counts;
- a bounded capacity recommendation.

Example:

```bash
GH_TOKEN='<read-only-token>' \
python scripts/runner_queue_metrics.py \
  --repo Aftergraph/rendetalje \
  --repo Aftergraph/aie \
  --per-page 30 \
  --target-p95-seconds 15 \
  --out runner-queue-metrics.json
```

The output schema is `aftergraph.runner-queue-metrics/1.0`.

## Interpretation

- `hold_capacity`: observed p95 is within target and no sampled job was cancelled.
- `add_or_free_one_warm_lane`: p95 is moderately above target.
- `scale_warm_pool_or_move_heavy_work_to_proof_pool`: p95 is materially above target.
- `insufficient_samples`: do not make a scaling claim.

The recommendation is advisory capacity guidance only. It is not authority,
approval, verification or permission to execute consequential work.

## Pilot observation

During the Rendetalje runner work on 2026-09-20, one sampled path had roughly
375 seconds of queue delay before the single-acquisition/shared-pool changes,
while a later sampled Verify job began about 11 seconds after workflow creation.
That is approximately a 34x improvement in those samples only. It is not an
organization-wide benchmark.
