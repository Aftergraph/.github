#!/usr/bin/env python3
"""Apply the org policy-sync manifest and report per-repo drift.

For each (file, repo) the manifest declares, compare the repo's copy against the
named template and report drift. In --apply mode, write the template into each
repo that differs. The sync workflow uses --apply then opens a PR per changed repo.

Usage:
  sync_policies.py --root DIR --manifest PATH [--topology PATH] [--apply] [--repo NAME]

--root is a workspace root with repos as siblings (mirrors the polyrepo layout).
Stdlib only; no network.
"""
from __future__ import annotations
import argparse, json, os, sys


def load_manifest(path):
    return json.load(open(path))


def repo_list(topology_path):
    topo = json.load(open(topology_path))
    return sorted(r["name"] for r in topo["repositories"])


def license_targets(manifest, repos):
    sec = manifest["license"]
    skip = set(sec.get("skip", []))
    overrides = sec.get("overrides", {})
    default = sec["default"]
    for repo in repos:
        if repo in skip:
            continue
        yield repo, overrides.get(repo, default)


def security_targets(manifest):
    sec = manifest["security"]
    skip = set(sec.get("skip", []))
    templates = sec["templates"]
    assignments = sec["assignments"]
    for group, repos in assignments.items():
        tmpl = templates[group]
        for repo in repos:
            if repo in skip:
                continue
            yield repo, tmpl


def file_label(repo, name):
    return f"{repo}/{name}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, help="workspace root (repos as siblings)")
    ap.add_argument("--manifest", required=True, help="policy-sync.json path")
    ap.add_argument("--topology", help="platform-topology/2.0.json path (for LICENSE default scope)")
    ap.add_argument("--apply", action="store_true", help="write templates into drifted repos")
    ap.add_argument("--repo", help="limit to one repo")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    manifest = load_manifest(args.manifest)
    base = os.path.dirname(os.path.abspath(args.manifest))

    targets = []  # (repo, file_name, template_abs_path)
    if args.topology:
        for repo, tmpl in license_targets(manifest, repo_list(args.topology)):
            targets.append((repo, "LICENSE", os.path.join(base, tmpl)))
    for repo, tmpl in security_targets(manifest):
        targets.append((repo, "SECURITY.md", os.path.join(base, tmpl)))

    drifted = []
    for repo, name, tmpl in sorted(targets):
        if args.repo and repo != args.repo:
            continue
        repo_dir = os.path.join(root, repo)
        dest = os.path.join(repo_dir, name)
        if not os.path.isdir(repo_dir):
            continue
        template = open(tmpl, "rb").read()
        current = open(dest, "rb").read() if os.path.exists(dest) else b""
        if current == template:
            continue
        status = "missing" if not os.path.exists(dest) else "drift"
        if args.apply:
            os.makedirs(repo_dir, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(template)
            print(f"APPLY  {file_label(repo, name):40} {status} -> {os.path.basename(tmpl)}")
        else:
            print(f"DRIFT  {file_label(repo, name):40} {status} (expected {os.path.basename(tmpl)})")
        drifted.append((repo, name))

    if not drifted:
        print("no drift detected")
    print(f"drifted={len(drifted)} apply={args.apply}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
