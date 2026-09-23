from __future__ import annotations

from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "maintain_runner_fabric_linux.sh"


class RunnerFabricMaintenanceTests(unittest.TestCase):
    def test_script_syntax(self) -> None:
        result = subprocess.run(
            ["bash", "-n", str(SCRIPT)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_safety_contract(self) -> None:
        s = SCRIPT.read_text(encoding="utf-8")

        required = [
            'case "$ACTION" in status|recycle-idle)',
            '[[ "${EUID:-$(id -u)}" -eq 0 ]] || fail "root_required"',
            'if (( used_before <= TMPFS_MAX_USED_PCT )); then',
            "pgrep -P \"$pid\" -f 'Runner\\.Worker'",
            'if (( workers > 0 )); then',
            'reason=active_worker_children',
            'if (( age < MIN_AGE_SECONDS )); then',
            'if (( memfd == 0 )); then',
            'systemctl restart "$unit"',
            '"$new_pid" != "$old_pid"',
            'RUNNER_FABRIC_MAINTENANCE=PASS',
            'RUNNER_FABRIC_MAINTENANCE=BLOCKED',
        ]
        for needle in required:
            self.assertIn(needle, s)

        forbidden = [
            "kill -9",
            "pkill",
            "systemctl restart '*'",
            "set -x",
            "sudo ",
        ]
        for needle in forbidden:
            self.assertNotIn(needle, s)

    def test_maintenance_is_pressure_and_idle_gated(self) -> None:
        s = SCRIPT.read_text(encoding="utf-8")
        pressure = s.index('if (( used_before <= TMPFS_MAX_USED_PCT )); then')
        worker_guard = s.index('if (( workers > 0 )); then')
        restart = s.index('systemctl restart "$unit"')
        self.assertLess(pressure, restart)
        self.assertLess(worker_guard, restart)


if __name__ == "__main__":
    unittest.main()
