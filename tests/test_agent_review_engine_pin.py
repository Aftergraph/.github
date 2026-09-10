"""Regression coverage for the reusable Sentinel engine self-pin."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "agent-review.yml"
FIXED_ENGINE_SHA = "b2ca4413435690222b34205ef232e3e6af0dc188"


def test_reusable_workflow_self_checkout_contains_cross_repo_path_fix() -> None:
    """Every central engine checkout must pin the commit containing PR #35."""
    workflow = WORKFLOW.read_text(encoding="utf-8")
    refs = re.findall(
        r"repository: Aftergraph/\.github\s*\n\s*ref: ([0-9a-f]{40})\b",
        workflow,
    )
    assert refs, "expected at least one pinned central engine checkout"
    assert set(refs) == {FIXED_ENGINE_SHA}
