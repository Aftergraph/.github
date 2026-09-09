# Aftergraph Brand Adoption Matrix

Authoritative inventory of every Aftergraph organization repository, its
Brand OS class, and its explicit adoption state.

- Inventory date: 2026-09-09 (re-queried via `gh repo list`; 25 repos observed,
  matching the checkpoint count — no additions, no removals).
- Canonical Brand OS source: `Aftergraph/brand`, release `1.1.0`
  (PR `Aftergraph/brand#20`, pending owner merge).
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
| brand | public | canonical | IN PROGRESS | Brand OS 1.1.0 source; PR #20 pending owner merge |
| .github | public | governance | NOT STARTED | Hosts this matrix; `brand/` tree is a competing source to convert to generated copies in Wave 3 |
| aftergraph.org | public | corporate | NOT STARTED | Org front door; missing favicon + manual token fork to fix |
| docs | public | corporate | NOT STARTED | Knowledge plane portal; migrate ABDE front-door wording with provenance |
| wi-frontend | private | product | NOT STARTED | Work Intelligence web experience; endorsed identity exists in Brand OS |
| wi-backend | public | technology | NOT STARTED | No logo; tokens + masterbrand only |
| studio | public | product | NOT STARTED | `packages/brand` local fork must move to versioned consumption; no break to consumers |
| sentinel | public | product | BLOCKED / NEEDS-REVIEW | Final product identity blocked: `Aftergraph/brand#19`, `Aftergraph/sentinel#7` |
| trust-gateway | public | technology | NOT STARTED | No logo; tokens + masterbrand only |
| runtime | private | technology | NOT STARTED | No logo; tokens + masterbrand only |
| model-registry | private | technology | NOT STARTED | No logo; tokens + masterbrand only |
| works-execution | public | technology | NOT STARTED | No logo; tokens + masterbrand only |
| aftergraph-cron-fabric | public | technology | NOT STARTED | No logo; tokens + masterbrand only |
| context-continuity | private | technology | NOT STARTED | Draft contract; no logo |
| after-graph-governance | public | governance | NOT STARTED | Cross-repo contracts; masterbrand only |
| intelligence-systems-research | public | research | NOT STARTED | SPEC-001 / MISSION-Bench program; research kit from Brand OS |
| llm-research-development | private | research | NOT STARTED | Methodology/evals; no logo |
| afm | private | research | NOT STARTED | Foundation-model research; no logo |
| aie | public | research | NOT STARTED | Draft 0.3 semantics; do NOT label an established standard |
| veranza | private | product | NOT STARTED | Internal hold, pre-clearance; no public identity work |
| autonomous-venture-company | private | product | NOT STARTED | Venture OS; adoption after public-surface decision |
| skills-vault | private | internal | NOT STARTED | Skill library; masterbrand only |
| sentinel-firetest | private | internal | EXEMPT | Throwaway live-fire proof; delete after use |
| sentinel-firetest2 | public | internal | EXEMPT | Suspected throwaway; verify purpose before any work, then delete or reclassify |
| continuum | private | product | NOT STARTED | Agentic continuity mission-bench; eval ally, no logo |

## Wave-5 priority order

1. `.github` 2. `aftergraph.org` 3. `docs` 4. `wi-frontend` 5. `wi-backend`
6. `studio` 7. `sentinel` (blocked identity excluded) 8. trust-gateway, runtime,
model-registry and shared technologies 9. research repositories
10. remaining public repositories.
