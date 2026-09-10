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

## Residual risks

- Token compromise can disable the workflow itself.
- Force-push history rewrites are flagged, not blocked.
- The agent never substitutes for human judgment on design or intent.
