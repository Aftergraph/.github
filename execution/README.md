# Aftergraph Polyrepo Exact-Head Manifest

`polyrepo-heads.json` is the bounded snapshot used by cross-repository gates.
Every repository entry binds a named role to one full `main` commit SHA. A
consumer must compare the snapshot to the exact tree it is about to test; a
mismatch is `STALE`, not an approximation of the current state.

The AIE dependency edge is explicit: its self-hosted workflow checks out
`Aftergraph/after-graph-governance` at the pinned SHA under
`.ci-dependencies/after-graph-governance`. A governance-main change therefore
requires a deliberate manifest/workflow refresh rather than silently changing
the test input.

Validate structure and exact expected heads:

```text
python scripts/verify_polyrepo_heads.py execution/polyrepo-heads.json
python scripts/verify_polyrepo_heads.py execution/polyrepo-heads.json \
  --head Aftergraph/aie=5c0adf20579e7de780c0331aa869ebe628b1bbed
```

Use `--remote` only when intentionally checking whether the captured snapshot
is still current on GitHub. A remote mismatch is expected after any main
commit and must be refreshed through review; it is never auto-repaired by a
runner.
