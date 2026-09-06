#!/usr/bin/env python3
"""Validate Aftergraph polyrepo exact-head manifests.

Usage:
  python scripts/verify_polyrepo_heads.py execution/polyrepo-heads.json
  python scripts/verify_polyrepo_heads.py execution/polyrepo-heads.json --head Aftergraph/aie=<sha>
  python scripts/verify_polyrepo_heads.py execution/polyrepo-heads.json --remote

`--remote` performs read-only `git ls-remote` calls and reports STALE when a
captured main SHA no longer matches GitHub. It never updates the manifest.
Stdlib only.
"""
import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SHA_RE = re.compile(r"^[a-f0-9]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+$")
REQUIRED_TOP = {"$id", "title", "description", "captured_at", "owner", "branch", "manifest_repository", "manifest_sha_policy", "repositories"}


def validate(doc):
    errors = []
    if not isinstance(doc, dict):
        return ["manifest must be an object"]
    missing = REQUIRED_TOP - set(doc)
    unknown = set(doc) - REQUIRED_TOP
    errors.extend(f"missing top-level field: {field}" for field in sorted(missing))
    errors.extend(f"unknown top-level field: {field}" for field in sorted(unknown))
    if errors:
        return errors
    if doc["$id"] != "contract:polyrepo-heads/1.0":
        errors.append("$id must be contract:polyrepo-heads/1.0")
    if doc["owner"] != "Aftergraph":
        errors.append("owner must be Aftergraph")
    if doc["manifest_repository"] != "Aftergraph/.github":
        errors.append("manifest_repository must be Aftergraph/.github")
    if not doc["manifest_sha_policy"].startswith("self-excluded:"):
        errors.append("manifest_sha_policy must declare self-excluded policy")
    if doc["branch"] != "main":
        errors.append("branch must be main")
    try:
        datetime.fromisoformat(doc["captured_at"].replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError):
        errors.append("captured_at must be ISO8601")
    repos = doc["repositories"]
    if not isinstance(repos, list) or not repos:
        return errors + ["repositories must be a non-empty array"]
    names = set()
    for index, entry in enumerate(repos):
        prefix = f"repositories[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(entry) != {"repo", "role", "sha", "dependencies"}:
            errors.append(f"{prefix} must contain exactly repo, role, sha, dependencies")
        repo, role, sha, dependencies = (entry.get(k) for k in ("repo", "role", "sha", "dependencies"))
        if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
            errors.append(f"{prefix}.repo must match owner/name")
        elif repo in names:
            errors.append(f"duplicate repository: {repo}")
        else:
            names.add(repo)
        if not isinstance(role, str) or not role:
            errors.append(f"{prefix}.role must be non-empty")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            errors.append(f"{prefix}.sha must be a full lowercase commit SHA")
        if not isinstance(dependencies, list):
            errors.append(f"{prefix}.dependencies must be an array")
            continue
        for dep_index, dep in enumerate(dependencies):
            dep_prefix = f"{prefix}.dependencies[{dep_index}]"
            if not isinstance(dep, dict) or set(dep) != {"repo", "sha", "path", "reason"}:
                errors.append(f"{dep_prefix} must contain exactly repo, sha, path, reason")
                continue
            if not isinstance(dep["repo"], str) or not REPO_RE.fullmatch(dep["repo"]):
                errors.append(f"{dep_prefix}.repo must match owner/name")
            if not isinstance(dep["sha"], str) or not SHA_RE.fullmatch(dep["sha"]):
                errors.append(f"{dep_prefix}.sha must be a full lowercase commit SHA")
            if not isinstance(dep["path"], str) or not dep["path"] or dep["path"].startswith("/"):
                errors.append(f"{dep_prefix}.path must be a non-absolute path")
            if not isinstance(dep["reason"], str) or not dep["reason"]:
                errors.append(f"{dep_prefix}.reason must be non-empty")
    return errors


def entries(doc):
    return {entry["repo"]: entry for entry in doc.get("repositories", [])}


def remote_head(repo):
    result = subprocess.run(
        ["git", "ls-remote", f"https://github.com/{repo}.git", "refs/heads/main"],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git ls-remote failed for {repo}")
    sha = result.stdout.split()[0] if result.stdout.split() else ""
    if not SHA_RE.fullmatch(sha):
        raise RuntimeError(f"no full main SHA returned for {repo}")
    return sha


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--head", action="append", default=[], metavar="REPO=SHA")
    parser.add_argument("--remote", action="store_true", help="read-only compare with GitHub main heads")
    args = parser.parse_args(argv)
    try:
        doc = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}")
        return 1
    errors = validate(doc)
    by_repo = entries(doc)
    for spec in args.head:
        if "=" not in spec:
            errors.append(f"--head must be REPO=SHA: {spec}")
            continue
        repo, sha = spec.split("=", 1)
        if repo not in by_repo:
            errors.append(f"unknown manifest repo: {repo}")
        elif not SHA_RE.fullmatch(sha):
            errors.append(f"--head SHA is invalid for {repo}")
        elif by_repo[repo]["sha"] != sha:
            errors.append(f"STALE: {repo} manifest={by_repo[repo]['sha'][:12]} supplied={sha[:12]}")
    if args.remote and not errors:
        for repo, entry in by_repo.items():
            try:
                live = remote_head(repo)
            except RuntimeError as exc:
                errors.append(f"REMOTE ERROR: {exc}")
                continue
            if live != entry["sha"]:
                errors.append(f"STALE: {repo} manifest={entry['sha'][:12]} remote={live[:12]}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"OK: {len(by_repo)} repositories, exact-head manifest captured at {doc['captured_at']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
