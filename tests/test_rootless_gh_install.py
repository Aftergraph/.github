"""Regression tests for rootless pinned GitHub CLI installation."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_pinned_gh.sh"
ACTION = ROOT / "actions" / "agent-review" / "action.yml"
VERSION = "2.46.0"
ARCHIVE = f"gh_{VERSION}_linux_amd64.tar.gz"


class RootlessGhInstallTests(unittest.TestCase):
    def _fake_release(self, root: Path, *, valid_checksum: bool = True) -> Path:
        release = root / "v2.46.0"
        payload = root / f"gh_{VERSION}_linux_amd64"
        binary = payload / "bin" / "gh"
        binary.parent.mkdir(parents=True)
        binary.write_text("#!/bin/sh\necho 'gh version 2.46.0'\n", encoding="utf-8")
        binary.chmod(0o755)
        release.mkdir(parents=True)
        archive = release / ARCHIVE
        with tarfile.open(archive, "w:gz") as tf:
            tf.add(payload, arcname=payload.name)
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        if not valid_checksum:
            digest = "0" * 64
        (release / f"gh_{VERSION}_checksums.txt").write_text(
            f"{digest}  {ARCHIVE}\n", encoding="utf-8"
        )
        return release.parent

    def _run(self, release_root: Path, install_dir: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update({
            "GH_VERSION": VERSION,
            "GH_RELEASE_BASE_URL": release_root.as_uri(),
            "GH_INSTALL_DIR": str(install_dir),
            "GH_ARCH": "amd64",
        })
        return subprocess.run(
            ["bash", str(INSTALLER)],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )
    def test_composite_uses_rootless_installer(self) -> None:
        action = ACTION.read_text(encoding="utf-8")
        self.assertIn("install_pinned_gh.sh", action)
        self.assertNotIn("sudo dpkg", action)

    def test_installs_verified_archive_without_privilege_escalation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release_root = self._fake_release(root)
            install_dir = root / "install"
            result = self._run(release_root, install_dir)
            self.assertEqual(result.returncode, 0, result.stderr)
            gh = install_dir / "gh"
            self.assertTrue(gh.is_file())
            self.assertTrue(os.access(gh, os.X_OK))
            self.assertIn("gh version 2.46.0", subprocess.check_output([gh], text=True))

    def test_rejects_archive_when_checksum_does_not_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            release_root = self._fake_release(root, valid_checksum=False)
            install_dir = root / "install"
            result = self._run(release_root, install_dir)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((install_dir / "gh").exists())


if __name__ == "__main__":
    unittest.main()
