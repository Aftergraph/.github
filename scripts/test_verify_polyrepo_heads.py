#!/usr/bin/env python3
"""Tests for verify_polyrepo_heads.py — stdlib unittest."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "verify_polyrepo_heads.py"
MANIFEST = ROOT / "execution" / "polyrepo-heads.json"


def load():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def run(doc, *args):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "manifest.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        return subprocess.run([sys.executable, str(VALIDATOR), str(path), *args], capture_output=True, text=True, cwd=ROOT)


class ManifestTest(unittest.TestCase):
    def test_current_manifest_is_valid(self):
        result = run(load())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("7 repositories", result.stdout)

    def test_schema_id_required(self):
        doc = load()
        del doc["$id"]
        result = run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing top-level field", result.stdout)

    def test_unknown_top_level_rejected(self):
        doc = load()
        doc["surprise"] = True
        result = run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown top-level", result.stdout)

    def test_bad_capture_time_rejected(self):
        doc = load()
        doc["captured_at"] = "later"
        result = run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ISO8601", result.stdout)

    def test_duplicate_repo_rejected(self):
        doc = load()
        doc["repositories"].append(copy.deepcopy(doc["repositories"][0]))
        result = run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("duplicate repository", result.stdout)

    def test_short_sha_rejected(self):
        doc = load()
        doc["repositories"][0]["sha"] = "bda0799"
        result = run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("full lowercase commit SHA", result.stdout)

    def test_dependency_requires_full_sha(self):
        doc = load()
        doc["repositories"][3]["dependencies"][0]["sha"] = "1deb274"
        result = run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("dependencies[0].sha", result.stdout)

    def test_dependency_path_must_be_relative(self):
        doc = load()
        doc["repositories"][3]["dependencies"][0]["path"] = "/absolute"
        result = run(doc)
        self.assertEqual(result.returncode, 1)
        self.assertIn("non-absolute", result.stdout)

    def test_expected_head_match(self):
        sha = load()["repositories"][3]["sha"]
        result = run(load(), "--head", f"Aftergraph/aie={sha}")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_expected_head_mismatch_is_stale(self):
        result = run(load(), "--head", "Aftergraph/aie=" + "0" * 40)
        self.assertEqual(result.returncode, 1)
        self.assertIn("STALE", result.stdout)

    def test_unknown_expected_repo_rejected(self):
        result = run(load(), "--head", "Aftergraph/unknown=" + "0" * 40)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown manifest repo", result.stdout)

    def test_malformed_expected_head_rejected(self):
        result = run(load(), "--head", "Aftergraph/aie=short")
        self.assertEqual(result.returncode, 1)
        self.assertIn("invalid", result.stdout)

    def test_dependency_edges_are_present(self):
        doc = load()
        aie = next(r for r in doc["repositories"] if r["repo"] == "Aftergraph/aie")
        self.assertEqual(aie["dependencies"][0]["repo"], "Aftergraph/after-graph-governance")
        self.assertEqual(aie["dependencies"][0]["path"], ".ci-dependencies/after-graph-governance")

    def test_invalid_json_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{nope", encoding="utf-8")
            result = subprocess.run([sys.executable, str(VALIDATOR), str(path)], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(result.returncode, 1)
        self.assertIn("INVALID", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=1)
