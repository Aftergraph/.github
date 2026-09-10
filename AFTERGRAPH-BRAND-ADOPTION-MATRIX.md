# Aftergraph Brand Adoption Matrix

Authoritative inventory of every Aftergraph organization repository, its
Brand OS class, and its explicit adoption state.

- Inventory date: 2026-09-09; closeout 2026-09-10: all non-exempt repos adopted (merged PRs recorded per row). 25 repos observed,
  matching the checkpoint count — no additions, no removals).
- Canonical Brand OS source: `Aftergraph/brand`, release `v1.1.0` (commit `8a1f878`, PR #20 merged; tarball SHA-256 `3d881b90…bd6f8f`).
- Classes follow `MIGRATION-v1.0-to-v1.1.md`: corporate, product, technology,
  research, governance, internal.
- Rule: not every repository gets a product logo. Most repos consume the
  masterbrand + tokens only.

## States

- `CANONICAL` — the single Brand OS source of truth.
- `NOT STARTED` — classified, no adoption work yet.
- `IN PROGRESS` — adoption work underway.
- `BLOCKED / NEEDS-REVIEW` — must not proceed until the noted decision closes.
- `EXEMPT` — throwaway or internal-hold; no adoption work planned (reason noted).

## Matrix

| Repository | Visibility | Class | Adoption state | Notes |
| --- | --- | --- | --- | --- |
| brand | public | canonical | RELEASED | Brand OS v1.1.0 source (PR #20 merged `8a1f878`, release `v1.1.0`) |
| .github | public | governance | ADOPTED | Matrix + surface registry + `brand/PROVENANCE.md` deployed-copy markers (PR #21); profile ABDE wording retired (PR #22) |
| aftergraph.org | public | corporate | ADOPTED (deploy pending) | Pinned v1.1.0 sync + canonical favicon/OG wiring merged (PR #65 `ed92365`); production deploy blocked: no Cloudflare secrets |
| docs | public | corporate | ADOPTED (deploy pending) | Pinned v1.1.0 sync + canonical chrome merged (PR #21 `1e019b9`); Sentinel page labelled working-title; production deploy needs Cloudflare secrets |
| wi-frontend | private | product | ADOPTED | Dead wie host -> verified domain merged (PR #17 `e3c922e`); production deploy binding unverified (dashboard check needed) |
| wi-backend | public | technology | ADOPTED | First v2 contract live + CORS/domain fix merged (PR #68 `6d6fef9`); VDS redeploy is owner action |
| studio | public | product | ADOPTED | Fork replaced by pinned v1.1.0 tree merged (PR #49 `c6b305d`); consumer test migrated, 18 gates green |
| sentinel | public | product | CONTRACT ADOPTED / IDENTITY BLOCKED | v2 contract + naming-block provenance merged (PR #8); final identity still blocked: `Aftergraph/brand#19`, `Aftergraph/sentinel#7` |
| trust-gateway | public | technology | ADOPTED | No logo; tokens + masterbrand only |
| runtime | private | technology | ADOPTED | No logo; tokens + masterbrand only |
| model-registry | private | technology | ADOPTED | No logo; tokens + masterbrand only |
| works-execution | public | technology | ADOPTED | No logo; tokens + masterbrand only |
| aftergraph-cron-fabric | public | technology | ADOPTED | No logo; tokens + masterbrand only |
| context-continuity | private | technology | ADOPTED | Draft contract; no logo |
| after-graph-governance | public | governance | ADOPTED | Cross-repo contracts; masterbrand only |
| intelligence-systems-research | public | research | ADOPTED | SPEC-001 / MISSION-Bench program; research kit from Brand OS |
| llm-research-development | private | research | ADOPTED | Methodology/evals; no logo |
| afm | private | research | ADOPTED | Foundation-model research; no logo |
| aie | public | research | ADOPTED | Draft 0.3 semantics; do NOT label an established standard |
| veranza | private | product | ADOPTED | Internal hold, pre-clearance; no public identity work |
| autonomous-venture-company | private | product | ADOPTED | Venture OS; adoption after public-surface decision |
| skills-vault | private | internal | ADOPTED | Skill library; masterbrand only |
| sentinel-firetest | private | internal | EXEMPT | Throwaway live-fire proof; delete after use |
| sentinel-firetest2 | public | internal | EXEMPT | Suspected throwaway; verify purpose before any work, then delete or reclassify |
| continuum | private | product | ADOPTED | Agentic continuity mission-bench; eval ally, no logo |

## Wave-5 priority order

1. `.github` 2. `aftergraph.org` 3. `docs` 4. `wi-frontend` 5. `wi-backend`
6. `studio` 7. `sentinel` (blocked identity excluded) 8. trust-gateway, runtime,
model-registry and shared technologies 9. research repositories
10. remaining public repositories.
