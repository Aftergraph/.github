#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Iterable

def scan_workflow_text(path: str, text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if "cancel-in-progress: true" in text:
        findings.append({
            "severity": "error",
            "code": "false-red-cancellation",
            "path": path,
            "message": "cancel-in-progress: true conflates superseded work with code failure history",
        })
    if "actions/checkout@v4" in text:
        findings.append({
            "severity": "warning",
            "code": "legacy-checkout-runtime",
            "path": path,
            "message": "checkout@v4 uses the deprecated Node-generation action runtime",
        })
    return findings

def scan_local(root: Path) -> list[dict[str, str]]:
    workflow_root = root / ".github" / "workflows"
    findings: list[dict[str, str]] = []
    if not workflow_root.is_dir():
        return findings
    for path in sorted(workflow_root.glob("*.y*ml")):
        findings.extend(scan_workflow_text(str(path.relative_to(root)), path.read_text(encoding="utf-8")))
    return findings

def github_code_search(query: str) -> list[dict[str, object]]:
    proc = subprocess.run(
        ["gh", "api", "-X", "GET", "/search/code", "-f", f"q={query}", "-f", "per_page=100"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"gh_code_search_failed:{proc.stderr.strip()[:300]}")
    return list(json.loads(proc.stdout).get("items", []))

def scan_org(owner: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    searches = [
        (
            f'org:{owner} "cancel-in-progress: true" path:.github/workflows',
            "error",
            "false-red-cancellation",
            "cancel-in-progress: true found on default branch",
        ),
        (
            f'org:{owner} "actions/checkout@v4" path:.github/workflows',
            "warning",
            "legacy-checkout-runtime",
            "checkout@v4 found on default branch",
        ),
    ]
    seen: set[tuple[str, str]] = set()
    for query, severity, code, message in searches:
        for item in github_code_search(query):
            repo = str((item.get("repository") or {}).get("full_name", ""))
            path = str(item.get("path", ""))
            key = (repo, path)
            if key in seen and code == "legacy-checkout-runtime":
                continue
            seen.add(key)
            findings.append({
                "severity": severity,
                "code": code,
                "path": f"{repo}/{path}",
                "message": message,
            })
    return findings

def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Aftergraph workflow queue/runtime policy.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--org")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--fail-on-error", action="store_true")
    args = parser.parse_args()

    findings = scan_local(Path(args.root).resolve())
    if args.org:
        findings.extend(scan_org(args.org))

    result = {
        "schema": "aftergraph.runner-fabric.audit/1.0",
        "findings": findings,
        "error_count": sum(f["severity"] == "error" for f in findings),
        "warning_count": sum(f["severity"] == "warning" for f in findings),
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for finding in findings:
            print(f"{finding['severity'].upper()} {finding['code']} {finding['path']}: {finding['message']}")
        print(f"errors={result['error_count']} warnings={result['warning_count']}")

    return 1 if args.fail_on_error and result["error_count"] else 0

if __name__ == "__main__":
    raise SystemExit(main())
