#!/usr/bin/env python3
"""Tests for the org policy-sync apply script.

Run: python scripts/test_sync_policies.py
Self-contained (stdlib unittest only, no network). Builds a throwaway workspace
in a temp directory and asserts about the syncer's observable contract:

  1. a repo whose file matches the template reports no drift;
  2. a missing LICENSE is detected and, on --apply, written to match the template;
  3. a drifted file is detected and, on --apply, corrected (idempotent re-run = 0 drift);
  4. a repo in the skip set is never touched even on --apply;
  5. an override template is applied instead of the default.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SYNCER = HERE / "sync_policies.py"
TEMPLATES = HERE.parent / "policies" / "templates"
APACHE = (TEMPLATES / "LICENSE-Apache-2.0").read_bytes()
MIT = (TEMPLATES / "LICENSE-MIT").read_bytes()
SECURITY_HARD = (TEMPLATES / "SECURITY-hard.md").read_bytes()


def write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def run(root: Path, manifest: Path, topology: Path, *args):
    return subprocess.run([sys.executable, str(SYNCER), "--root", str(root),
                           "--manifest", str(manifest), "--topology", str(topology), *args],
                          capture_output=True, text=True)


def make_topology(root: Path, names):
    topo = {"$schema": "./2.0.schema.json", "schema_version": "platform-topology/2.0",
            "organization": "Aftergraph", "evidence_cut": "2026-09-13",
            "description": "test", "repositories": [{"name": n, "canonical_branch": "main",
            "visibility": "public", "architecture_plane": None, "system_class": "x",
            "role": "r", "lifecycle": "active", "owns": "o", "must_not_own": "n"} for n in names]}
    p = root / "topology.json"
    write(p, json.dumps(topo).encode())
    return p


class SyncTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ws = self.tmp / "ws"
        self.ws.mkdir()
        (self.tmp / "templates").mkdir()
        (self.tmp / "templates" / "LICENSE-Apache-2.0").write_bytes(APACHE)
        (self.tmp / "templates" / "LICENSE-MIT").write_bytes(MIT)
        (self.tmp / "templates" / "SECURITY-hard.md").write_bytes(SECURITY_HARD)
        self.manifest = self.tmp / "policy-sync.json"
        write(self.manifest, json.dumps({
            "license": {"default": "templates/LICENSE-Apache-2.0",
                        "overrides": {"mit-repo": "templates/LICENSE-MIT"}, "skip": ["no-license"]},
            "security": {"templates": {"hard": "templates/SECURITY-hard.md"},
                         "assignments": {"hard": ["hard-repo"]},
                         "skip": ["bespoke-repo"]}}).encode())
        self.topology = make_topology(self.tmp, ["match-repo", "drift-repo", "no-license",
                                                 "mit-repo", "hard-repo", "bespoke-repo"])

    def tearDown(self):
        self._tmp.cleanup()

    def test_matching_file_reports_no_drift(self):
        write(self.ws / "match-repo" / "LICENSE", APACHE)
        r = run(self.ws, self.manifest, self.topology, "--repo", "match-repo")
        self.assertEqual(r.returncode, 0)
        self.assertIn("no drift detected", r.stdout)

    def test_missing_license_detected_and_written_on_apply(self):
        (self.ws / "drift-repo").mkdir()
        r = run(self.ws, self.manifest, self.topology, "--apply", "--repo", "drift-repo")
        self.assertIn("APPLY", r.stdout)
        self.assertEqual((self.ws / "drift-repo" / "LICENSE").read_bytes(), APACHE)

    def test_apply_is_idempotent(self):
        (self.ws / "drift-repo").mkdir()
        run(self.ws, self.manifest, self.topology, "--apply", "--repo", "drift-repo")
        r = run(self.ws, self.manifest, self.topology, "--repo", "drift-repo")
        self.assertIn("no drift detected", r.stdout)
        self.assertIn("drifted=0", r.stdout)

    def test_skip_repo_security_preserved_on_apply(self):
        # bespoke-repo is skipped for SECURITY but not LICENSE, so its bespoke
        # SECURITY.md must survive while LICENSE is synced to the default.
        write(self.ws / "bespoke-repo" / "LICENSE", b"old\n")
        write(self.ws / "bespoke-repo" / "SECURITY.md", b"bespoke security\n")
        r = run(self.ws, self.manifest, self.topology, "--apply", "--repo", "bespoke-repo")
        self.assertIn("APPLY  bespoke-repo/LICENSE", r.stdout)
        self.assertEqual((self.ws / "bespoke-repo" / "SECURITY.md").read_bytes(), b"bespoke security\n")
        self.assertEqual((self.ws / "bespoke-repo" / "LICENSE").read_bytes(), APACHE)

    def test_override_template_applied(self):
        (self.ws / "mit-repo").mkdir()
        run(self.ws, self.manifest, self.topology, "--apply", "--repo", "mit-repo")
        self.assertEqual((self.ws / "mit-repo" / "LICENSE").read_bytes(), MIT)
    def test_license_skip_repo_not_touched(self):
        write(self.ws / "no-license" / "LICENSE", b"keep me\n")
        r = run(self.ws, self.manifest, self.topology, "--apply", "--repo", "no-license")
        self.assertIn("no drift detected", r.stdout)
        self.assertEqual((self.ws / "no-license" / "LICENSE").read_bytes(), b"keep me\n")

    def test_security_assignment_applied(self):
        (self.ws / "hard-repo").mkdir()
        r = run(self.ws, self.manifest, self.topology, "--apply", "--repo", "hard-repo")
        self.assertIn("APPLY", r.stdout)
        self.assertEqual((self.ws / "hard-repo" / "SECURITY.md").read_bytes(), SECURITY_HARD)


if __name__ == "__main__":
    unittest.main()
