# Agent Review — operator guide

The code-review agent (COMMENT-ONLY permanently) verifies PRs against
pinned checks, approval binding, and seam rules, and emits review
packets. It posts nothing: no comments, no approvals, no statuses.

## Triggers

| Event | Job | Effect |
|---|---|---|
| `pull_request_target` opened/synchronize/ready_for_review | `review` | Emits packet JSON to stdout + per-PR file artifact |
| `merge_group` checks_requested | `review` | Same, on the queue head |
| `push` to `main` | `push_audit` | Detective only: fails visibly on NON_PR_HEAD |
| `workflow_dispatch` with PR URL | `review` | Manual re-run |

## Verdict semantics

- `MERGEABLE`: delta clean, all pinned checks green, binding valid, seams pass.
- `BLOCKED` + reason codes: `DELTA_MISMATCH`, `PINNED_CHECK_*`,
  `NO_CI_PROTECTION`, `PUSH_AFTER_REVIEW`, `UNRESOLVED_CONVERSATIONS`,
  `CODEOWNERS_UNMATCHED`, `SEAM_*`, `NON_PR_HEAD` (push audit only).
- Any ERROR/UNKNOWN fails closed to BLOCKED. Exit 0 on packet emit,
  1 on audit finding, 2 on tool errors.

## Packet artifact filename

The per-PR file is `<repo-slug>-<number>-<head-sha7>.json` and the upload
step globs `<emit-dir>/*.json`. `upload-artifact` skips hidden files and
never matches dot-prefixed names, so the repo slug strips leading dots
(`.github` → `github`, packet payload still says `.github`). A dot-prefixed
file name makes the upload step fail with "No files were found", i.e. every
PR in the `.github` repo itself fails the gate — keep slugs visible.

## Override label

Repos with no CI (currently `autonomous-venture-company`) stay BLOCKED
with `NO_CI_PROTECTION` unless the PR carries the
`OWNER_OVERRIDE_ACCEPT_RISK` label. Only the owner applies it, knowingly
accepting the risk. Unknown labels never override.

## Push audit (private repos)

No enforceable branch protection exists on private Free-tier repos, so
`push_audit` detects direct-to-main pushes: a main head with no merged
associated PR fails the job visibly. Detective, not preventive — treat
a red audit as stop-the-line. No Pro spend is assumed.

## Sentinel brand mapping

This gate is the merge-side half of **Sentinel by Aftergraph**
(`Aftergraph/sentinel` repo: deterministic verdict engine, rulepacks,
receipts `sentinel.receipt/0.1`, JSONL ledger). Division of labor:

- Sentinel `lib/` decides findings and verdicts from diffs (SHIP /
  DO_NOT_SHIP / STALE / BLOCKED); this gate enforces merge mechanics
  (delta-vs-head, pinned checks, approval binding) and emits packets.
- Verdict map: gate `MERGEABLE` ≈ Sentinel `SHIP`; gate `BLOCKED` ≈
  `BLOCKED`/`DO_NOT_SHIP`; gate `DELTA_MISMATCH` ≈ Sentinel `STALE`
  (freshness wins, never silently green — same law both sides).
- Override map: gate label `OWNER_OVERRIDE_ACCEPT_RISK` is the
  coarse GitHub-side twin of Sentinel's recorded override
  (`--override` + actor + reason). The label carries no reason string —
  that is a known gap: use it only with a reason stated in the PR
  thread. Like Sentinel, overrides never apply to STALE/delta-mismatch.
- Receipt seam (not dependency): when a Sentinel receipt exists for
  the same repo+PR+head, its ID SHOULD be recorded in the packet;
  the gate never requires Sentinel to run and Sentinel never requires
  the gate. Either side works alone.

## Engine pin maintenance

The workflow checks out its own engine repo by exact SHA
(`sentinel-engine`). Whenever `actions/`, `scripts/` or `policies/`
change on main, open a follow-up PR bumping the three `ref:` pins in
`.github/workflows/agent-review.yml` to the new main SHA, then re-pin
all per-repo callers the same way. The T11 tests fail if the ref is
not a 40-hex SHA.

## Residual risks

- Token compromise can disable the workflow itself.
- Force-push history rewrites are flagged, not blocked.
- The agent never substitutes for human judgment on design or intent.
