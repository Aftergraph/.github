# RFC 0001: Org-wide CI authority boundary

Status: proposed · Author: Fo (for @JonasAbde) · Date: 2026-10-01

## Decision

Adopt the AVC boundary for all of Aftergraph: **GitHub is Git/PR/status transport only. Authoritative CI evidence is a commit status posted from Aftergraph-owned hosts.** GitHub Actions results become observational. Reference implementation: `autonomous-venture-company/docs/runbooks/github-actions-zero-dependency.md` and `tools/avc-runner-bridge`.

## Current state (measured 2026-10-01)

| Fact | Value |
|---|---|
| Org plan | GitHub Free |
| Repos (non-archived) | 45: 18 public, 27 private (incl. runtime, relay) |
| Active workflows | runtime, relay, ISR, aftergraph.org 30 each; works-execution 25; aie 24; sentinel 23; only AVC and sentinel-firetest2 have 0 |
| AVC bridge | `avc-runner-bridge.service` active on vmi3517816 since 2026-10-01 17:43 CEST. Runs are label-triggered only: `avc-ci:run` on a PR or `avc-ci:main-run` on control issue #759, applied by `JonasAbde`. Main commits `6c474b9` and `f66bf22` have no `avc/ci-local` because nobody triggered them. Latest terminal results: #1051 `avc-ci:error` (2026-09-30), #1038 `avc-ci:error` (2026-09-20) |
| Bridge scope | single repo: `src/constants.ts` hardcodes `REPOSITORY`, `AUTHORIZED_ACTOR = "JonasAbde"`, the `avc-ci:*` labels and control issue 759 |
| Self-hosted runners | online: vps-ci-01, vds-aftergraph-ci-relay, vds-aftergraph-ci-runtime; offline: JONAS-LENOVO-runtime-acceptance, lenovo-relay-windows |
| Observability | CI user `agci` cannot read the bridge journal or `/var/lib/avc-runner-bridge`; relay MCP gateway returns Unauthorized |

## Challenges and solutions

### 1. The org runs on Actions today
**Solution: phased, per-repo opt-in.** A repo joins when it has `ci/local-runner/run-local-ci.sh <sha>` (same contract as AVC) and is listed in the bridge allowlist. Its workflows stay as observational until its local status has been green on main for 7 days; then workflows are removed and `assert-github-actions-zero-dependency.sh` is added.
Order: low-workflow private repos first (core, concord, skillport, model-registry), then runtime, relay, ISR, the public web repos last.

### 2. The bridge only knows AVC
**Solution: generalize to `aftergraph-runner-bridge`.**
- Replace the `REPOSITORY` constant with an allowlist file `/etc/aftergraph-ci/repos.json` (`repo`, `verifier`, `lane`, `timeout`).
- Key ledger, lock and lanes by repo. Keep repo identity validation, now against the allowlist.
- Post one context per repo: `aftergraph/ci-local` (AVC keeps `avc/ci-local` as an alias during transition).
- Keep it outbound-only and polling; no inbound webhooks.

### 3. One VPS is a single point of failure
**Solution: two hosts, one claim.**
- Run the bridge on a second host (Lenovo once back online, or a second small VPS). The existing label-based claim on GitHub is the distributed lock; add a claim TTL so a dead host's claim expires.
- Bridge posts a heartbeat status (`aftergraph/bridge-heartbeat`) on a fixed ref every poll; Fo's daily audit alerts when it is older than 30 min.
- An outage means "no evidence yet", never "pass". Merges wait.

### 4. Free plan cannot require statuses on private repos
**Solution: enforce where GitHub allows, detect everywhere else.**
- Public repos (18): ruleset requiring `aftergraph/ci-local` from the sentinel GitHub App (app 5144112) as the only allowed source.
- Private repos (27): merges go only through the gate (`merge-pr.sh` pattern: verify exact head SHA has a green authoritative status, then squash). Add a post-merge detector to the daily audit: any default-branch commit without a green authoritative status on its PR head is flagged, and a revert PR is opened automatically.
- Optional, owner decision: GitHub Team makes the private-repo rule server-side. It is a purchase, so it stays with @JonasAbde.

### 5. Bypasses undermine the boundary
**Solution: one merge path, including for agents.**
- Fo merges only through the gate. No direct API merges (as happened with AVC #1052 on 2026-10-01).
- Remove the admin-role bypass added to ISR ruleset `merge-queue-main` (22410215) once the ISR gate exists, and replace the review requirement with the authoritative status (solo code owner cannot self-approve).

### 6. CodeQL and code scanning are Actions-based
**Solution: split by visibility.**
- Public repos: run CodeQL CLI on the host and upload SARIF via the code-scanning API, or keep the CodeQL workflow as observational-only.
- Private repos: code scanning is not available on Free. Run `osv-scanner` and `semgrep` inside `run-local-ci.sh` and fail the status on high/critical findings.

### 7. Bridge evidence is hard to read and runs need a human trigger
**Solution: readable evidence without root, and automatic triggering.**
- Trigger on every PR head and every main push automatically, instead of only when `JonasAbde` applies a label. Keep the label as a manual re-run.
- Make the authorized actor a list (owner plus the sentinel App) so an agent can trigger without borrowing the owner identity.
- Create group `aftergraph-ops`; add `agci`. Grant it read on `/var/log/<bridge>` and the ledger (or `systemd-journal` group membership).
- Bridge writes a sanitized JSON status file (last poll, last claim, last error) readable by that group.
- Renew the relay MCP gateway bearer so Fo can inspect through the execution gateway.

## Owner actions (root or purchase)

1. Add `agci` to `systemd-journal` or a new `aftergraph-ops` group with read on `/var/lib/avc-runner-bridge` (unblocks diagnosing the silent AVC bridge today).
2. Renew the relay MCP gateway bearer token.
3. Decide on GitHub Team (optional; detection covers the gap without it).
4. Bring a second bridge host online.

## Fo actions (no owner input needed)

1. Find out why #1051 and #1038 ended in `avc-ci:error` once (1) is done.
2. Generalize the bridge (section 2) as a PR in autonomous-venture-company.
3. Add the post-merge detector and heartbeat check to the daily audit.
4. Pilot the boundary on one low-workflow private repo.
