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

    def _base_env(self, fabric_root: Path, tmp_path: Path) -> dict[str, str]:
        env = os.environ.copy()
        env.update(
            {
                "AFTERGRAPH_RUNNER_ROOT": str(fabric_root),
                "AFTERGRAPH_RUNNER_COUNT": "1",
                "AFTERGRAPH_RUNNER_VERIFY_GITHUB": "0",
                "AFTERGRAPH_RUNNER_CHECK_TMPFS": "1",
                "AFTERGRAPH_RUNNER_TMPFS_PATH": str(tmp_path),
                "AFTERGRAPH_RUNNER_TMPFS_MAX_USED_PCT": "99",
                "AFTERGRAPH_RUNNER_TMPFS_MIN_FREE_INODES": "0",
            }
        )
        return env

    def test_service_status_runs_from_runner_root_and_tmpfs_is_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fabric_root = temp_path / "fabric"
            self._write_runner(fabric_root)

            env = self._base_env(fabric_root, temp_path)
            result = subprocess.run(
                ["bash", str(DOCTOR)],
                cwd=temp_path,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertIn("RUNNER_FABRIC_READY=1/1", result.stdout)
            self.assertIn("RUNNER_TMPFS_HEALTH=PASS", result.stdout)
            self.assertIn("RUNNER_FABRIC_DOCTOR=PASS", result.stdout)

    def test_tmpfs_pressure_is_infrastructure_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fabric_root = temp_path / "fabric"
            self._write_runner(fabric_root)

            bin_dir = temp_path / "bin"
            bin_dir.mkdir()
            fake_df = bin_dir / "df"
            fake_df.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "if [[ \"$1\" == \"-Pk\" ]]; then\n"
                "  printf 'Filesystem 1024-blocks Used Available Capacity Mounted on\\n'\n"
                "  printf 'tmpfs 100 100 0 100%% %s\\n' \"$2\"\n"
                "else\n"
                "  printf 'Filesystem Inodes IUsed IFree IUse%% Mounted on\\n'\n"
                "  printf 'tmpfs 100000 1 99999 1%% %s\\n' \"$2\"\n"
                "fi\n",
                encoding="utf-8",
            )
            fake_df.chmod(0o755)

            env = self._base_env(fabric_root, temp_path)
            env["PATH"] = f"{bin_dir}:{env['PATH']}"
            env["AFTERGRAPH_RUNNER_TMPFS_MAX_USED_PCT"] = "85"

            result = subprocess.run(
                ["bash", str(DOCTOR)],
                cwd=temp_path,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
            self.assertIn("RUNNER_TMPFS_USED_PCT=100", result.stdout)
            self.assertIn("RUNNER_TMPFS_HEALTH=FAIL reason=space_pressure", result.stdout)
            self.assertNotIn("RUNNER_FABRIC_DOCTOR=PASS", result.stdout)

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

            env = self._base_env(fabric_root, temp_path)
            env.update(
                {
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
            self.assertIn("RUNNER_TMPFS_HEALTH=PASS", result.stdout)
            self.assertNotIn(env["GH_TOKEN"], result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
