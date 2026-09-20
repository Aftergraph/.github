from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "runner_fabric_metrics.py"
spec = importlib.util.spec_from_file_location("runner_fabric_metrics", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)

class RunnerFabricMetricsTests(unittest.TestCase):
    def test_summary_separates_queue_pressure_from_cancellation(self) -> None:
        runs = [
            {
                "id": 1,
                "status": "completed",
                "conclusion": "success",
                "created_at": "2026-09-20T10:00:00Z",
            },
            {
                "id": 2,
                "status": "completed",
                "conclusion": "cancelled",
                "created_at": "2026-09-20T10:01:00Z",
            },
        ]
        jobs = {
            1: [{
                "started_at": "2026-09-20T10:00:05Z",
                "completed_at": "2026-09-20T10:00:25Z",
                "runner_name": "runner-a",
            }],
            2: [{
                "started_at": "2026-09-20T10:01:45Z",
                "completed_at": "2026-09-20T10:01:50Z",
                "runner_name": "runner-b",
            }],
        }
        summary = module.summarize(runs, jobs, queue_target_seconds=15)
        self.assertEqual(summary["queue_seconds"]["p50"], 25.0)
        self.assertGreater(summary["queue_seconds"]["p95"], 15.0)
        self.assertEqual(summary["cancellation_rate"], 0.5)
        self.assertEqual(summary["capacity_signal"], "pressure")
        self.assertEqual(summary["observed_runners"], ["runner-a", "runner-b"])

    def test_empty_summary_is_safe(self) -> None:
        summary = module.summarize([], {})
        self.assertIsNone(summary["queue_seconds"]["p95"])
        self.assertEqual(summary["cancellation_rate"], 0.0)
        self.assertEqual(summary["capacity_signal"], "within_target")

if __name__ == "__main__":
    unittest.main()
