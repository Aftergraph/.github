from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCTOR = ROOT / "scripts" / "doctor_runner_fabric_linux.sh"


class RunnerFabricDoctorTests(unittest.TestCase):
    def make_runner(self, root: Path, index: int) -> None:
        home = root / f"runner-{index}"
        home.mkdir(parents=True)
        (home / ".runner").write_text('{"runnerId":123}\n', encoding="utf-8")
        (home / "run.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        svc = home / "svc.sh"
        svc.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            '[[ "$PWD" == "$(cd "$(dirname "$0")" && pwd)" ]] || { echo wrong-cwd >&2; exit 3; }\n'
            'echo "active (running)"\n',
            encoding="utf-8",
        )
        os.chmod(home / "run.sh", 0o755)
        os.chmod(svc, 0o755)

    def test_service_status_runs_from_runner_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self.make_runner(root, 1)
            env = os.environ.copy()
            env.update(
                {
                    "AFTERGRAPH_RUNNER_ROOT": str(root),
                    "AFTERGRAPH_RUNNER_COUNT": "1",
                }
            )
            proc = subprocess.run(
                ["bash", str(DOCTOR)],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("RUNNER_FABRIC_READY=1/1", proc.stdout)
            self.assertIn("RUNNER_FABRIC_DOCTOR=PASS", proc.stdout)

    def test_org_visibility_tsv_parser(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "fabric"
            self.make_runner(root, 1)
            bindir = Path(td) / "bin"
            bindir.mkdir()
            gh = bindir / "gh"
            gh.write_text(
                "#!/usr/bin/env bash\n"
                "printf 'aftergraph-ci-1-host\\tonline\\tfalse\\tself-hosted,Linux,X64,aftergraph-ci\\n'\n",
                encoding="utf-8",
            )
            os.chmod(gh, 0o755)

            env = os.environ.copy()
            env.update(
                {
                    "PATH": f"{bindir}:{env['PATH']}",
                    "GH_TOKEN": "test-only",
                    "AFTERGRAPH_RUNNER_ROOT": str(root),
                    "AFTERGRAPH_RUNNER_COUNT": "1",
                    "AFTERGRAPH_RUNNER_VERIFY_GITHUB": "1",
                }
            )
            proc = subprocess.run(
                ["bash", str(DOCTOR)],
                env=env,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("GITHUB_ORG_VISIBLE_READY=1/1", proc.stdout)
            self.assertIn("RUNNER_FABRIC_DOCTOR=PASS", proc.stdout)


if __name__ == "__main__":
    unittest.main()
