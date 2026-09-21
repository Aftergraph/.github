from __future__ import annotations

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts" / "doctor_runner_fabric_linux.sh"


class RunnerFabricDoctorTests(unittest.TestCase):
    def _write_runner(self, fabric_root: Path) -> Path:
        runner_root = fabric_root / "runner-1"
        runner_root.mkdir(parents=True)
        (runner_root / ".runner").write_text('{"runnerId":1}\n', encoding="utf-8")

        run_sh = runner_root / "run.sh"
        run_sh.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        run_sh.chmod(0o755)

        svc_sh = runner_root / "svc.sh"
        svc_sh.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "[[ \"$PWD\" == \"$(cd \"$(dirname \"$0\")\" && pwd)\" ]]\n"
            "printf 'active (running)\\n'\n",
            encoding="utf-8",
        )
        svc_sh.chmod(0o755)
        return runner_root

    def test_service_status_runs_from_runner_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            fabric_root = Path(temp_dir) / "fabric"
            self._write_runner(fabric_root)

            env = os.environ.copy()
            env.update(
                {
                    "AFTERGRAPH_RUNNER_ROOT": str(fabric_root),
                    "AFTERGRAPH_RUNNER_COUNT": "1",
                    "AFTERGRAPH_RUNNER_VERIFY_GITHUB": "0",
                }
            )
            result = subprocess.run(
                ["bash", str(DOCTOR)],
                cwd=Path(temp_dir),
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("RUNNER_FABRIC_READY=1/1", result.stdout)
            self.assertIn("RUNNER_FABRIC_DOCTOR=PASS", result.stdout)

    def test_github_inventory_is_parsed_as_tsv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fabric_root = temp_path / "fabric"
            self._write_runner(fabric_root)

            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            gh = bin_dir / "gh"
            gh.write_text(
                "#!/usr/bin/env bash\n"
                "printf 'aftergraph-ci-1-host\\tonline\\tfalse\\tself-hosted,Linux,X64,aftergraph-ci\\n'\n",
                encoding="utf-8",
            )
            gh.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "AFTERGRAPH_RUNNER_ROOT": str(fabric_root),
                    "AFTERGRAPH_RUNNER_COUNT": "1",
                    "AFTERGRAPH_RUNNER_VERIFY_GITHUB": "1",
                    "GH_TOKEN": "test-token-not-logged",
                    "PATH": f"{bin_dir}:{env['PATH']}",
                }
            )
            result = subprocess.run(
                ["bash", str(DOCTOR)],
                cwd=temp_path,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("GITHUB_ORG_VISIBLE_READY=1/1", result.stdout)
            self.assertNotIn(env["GH_TOKEN"], result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
