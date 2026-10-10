"""The packet artifact upload must not decide the review outcome.

Artifact storage is an organisation-wide quota. When it was full,
actions/upload-artifact failed with "Artifact storage quota has been hit"
and every caller's required "sentinel-gate / review (read-only)" check went
red although the review itself completed. These tests pin the fix: the
upload is non-fatal, the packet is recorded in the job summary, and a run
that emits no packet still fails closed.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION = ROOT / "actions" / "agent-review" / "action.yml"


def steps(text: str) -> list[str]:
    """Split the composite `runs.steps` list into raw per-step blocks."""
    body = text.split("\n  steps:\n", 1)[1]
    return [block for block in re.split(r"\n(?=    - )", "\n" + body) if block.strip()]


def step(text: str, name: str) -> str:
    matches = [b for b in steps(text) if re.search(rf"name: {re.escape(name)}\s*\n", b)]
    assert len(matches) == 1, f"expected one step named {name!r}, got {len(matches)}"
    return matches[0]


def run_block(block: str) -> str:
    lines = block.split("\n")
    start = next(i for i, line in enumerate(lines) if re.fullmatch(r"\s+run: \|", line))
    indent = len(lines[start]) - len(lines[start].lstrip())
    body = []
    for line in lines[start + 1:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line)
    return textwrap.dedent("\n".join(body))


class UploadQuotaTest(unittest.TestCase):
    def setUp(self) -> None:
        self.action = ACTION.read_text(encoding="utf-8")

    def test_upload_step_is_non_fatal(self) -> None:
        upload = step(self.action, "Upload packet file artifact")
        self.assertIn("actions/upload-artifact@", upload)
        self.assertRegex(upload, r"\n\s+id: upload-packet\n")
        self.assertRegex(upload, r"\n\s+continue-on-error: true\n")

    def test_only_the_upload_may_continue_on_error(self) -> None:
        tolerant = [b for b in steps(self.action) if "continue-on-error" in b]
        self.assertEqual(len(tolerant), 1)
        self.assertIn("actions/upload-artifact@", tolerant[0])

    def test_review_steps_stay_fatal_and_ordered(self) -> None:
        names = [re.search(r"name: (.+)", b).group(1).strip() for b in steps(self.action)]
        for required in ("Collect PR data (read-only API)",
                         "Emit review packet (stdout plus per-PR file)",
                         "Verify packet file was emitted",
                         "Record packet in job summary",
                         "Upload packet file artifact"):
            self.assertIn(required, names)
        self.assertLess(names.index("Emit review packet (stdout plus per-PR file)"),
                        names.index("Verify packet file was emitted"))
        self.assertLess(names.index("Verify packet file was emitted"),
                        names.index("Upload packet file artifact"))
        for name in names[:names.index("Upload packet file artifact")]:
            block = step(self.action, name)
            self.assertNotIn("continue-on-error", block, name)
            self.assertNotRegex(block, r"\n\s+if: ", f"{name} must always run")

    def test_skipped_upload_is_reported_as_warning(self) -> None:
        report = step(self.action, "Report skipped artifact upload")
        self.assertIn("if: steps.upload-packet.outcome == 'failure'", report)
        self.assertIn("::warning::", report)
        self.assertNotIn("exit 1", report)

    def _bash(self, name: str, emit_dir: str, summary: str) -> subprocess.CompletedProcess:
        env = dict(os.environ, EMIT_DIR=emit_dir, GITHUB_STEP_SUMMARY=summary)
        return subprocess.run(["bash", "-c", run_block(step(self.action, name))],
                              env=env, capture_output=True, text=True)

    def test_missing_packet_still_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            summary = str(Path(tmp) / "summary.md")
            emit = Path(tmp) / "emit"
            emit.mkdir()
            res = self._bash("Verify packet file was emitted", str(emit), summary)
            self.assertEqual(res.returncode, 1)
            self.assertIn("emitted no packet", res.stdout)
            (emit / "Lume-1-abc.json").write_text("{}", encoding="utf-8")
            self.assertEqual(self._bash("Verify packet file was emitted", str(emit), summary).returncode, 0)

    def test_summary_records_verdict_and_packet(self) -> None:
        packet = {"repo": "Lume", "number": 7, "head_sha": "a" * 40,
                  "agent_review": {"verdict": "BLOCKED", "reason_codes": ["PINNED_CHECK_MISSING"]}}
        with tempfile.TemporaryDirectory() as tmp:
            emit = Path(tmp) / "emit"
            emit.mkdir()
            (emit / "Lume-7-aaaaaaa.json").write_text(json.dumps(packet), encoding="utf-8")
            summary = Path(tmp) / "summary.md"
            res = self._bash("Record packet in job summary", str(emit), str(summary))
            self.assertEqual(res.returncode, 0, res.stderr)
            text = summary.read_text(encoding="utf-8")
            self.assertIn("verdict: `BLOCKED`", text)
            self.assertIn("PINNED_CHECK_MISSING", text)
            self.assertIn('"head_sha": "' + "a" * 40 + '"', text)


if __name__ == "__main__":
    unittest.main()
