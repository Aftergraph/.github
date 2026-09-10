# Agent Review — Operator Guide (slice 3 final)

Agent home: `Aftergraph/.github`. Authority: **COMMENT-only permanently**
(per `v4-execution/agent-review-decisions.md` D2). The agent never APPROVEs
and never writes `reviews[]`. It emits `agent_verdict` (`MERGEABLE` /
`BLOCKED`) plus a human COMMENT body. **This slice posts NOTHING itself
(emit only)**: the workflow and composite action emit review-packet JSON to
stdout; a human (or a later, explicitly authorized slice) decides whether
and what to post.

No owner money spent (D3): the agent check-run is the only gate plus
direct-to-main push detection. No GitHub Pro / push-protection spend.

## Triggers

Workflow: `.github/workflows/agent-review.yml` (permissions are read-only:
`contents: read`, `checks: read`, `pull-requests: read` — no `write`
scopes).

| Event | Config | What runs | Notes |
|---|---|---|---|
| `pull_request_target` (`opened`, `synchronize`, `ready_for_review`) | checkout pins the **base** SHA; PR head is never checked out | `review` (agent packet, emit-only) + `selftest` | Normal PR gate path. |
| `merge_group` (`checks_requested`) | merge-queue temp commit (`github.sha`) | `selftest` is the blocking gate; `review` emits merge-queue context JSON only (no PR URL exists on `merge_group`) | Merge-queue support: the queue stays green via unit tests; per-PR verdicts remain the merge signal (see residue risks). |
| `push` to `main` | `push-audit` job, `if: github.event_name == 'push'` | `scripts/audit_push.py` on the pushed head | Detective audit only (below). Other jobs skip on `push`. |
| `workflow_dispatch` (`pr_url`) | manual re-run with a full PR URL | `review` + `selftest` | Re-run a single PR without pushing. |

## Verdict semantics

`scripts/agent_review.py` reads the reviewed 14-field packet, the live head
SHA, live checks, and PR labels; it prints the packet plus an additive
`agent_review` block (`name`, `version`, `run_id`, `reviewed_head_sha`,
`current_head_sha`, `delta_clean`, `verdict`, `reason_codes`). Exit 0
whenever a packet is emitted; non-zero only on tool errors. Old readers
ignore the additive block (14 required packet fields unchanged; schema
`review-packet/0.3`).

| Verdict | Meaning |
|---|---|
| `MERGEABLE` | Delta clean **and** every pinned check green — **or** AVC empty-pin set with an explicit `OWNER_OVERRIDE_ACCEPT_RISK` label recorded (never silent). |
| `BLOCKED` | Anything else. Read `reason_codes`. |

Reason codes:

| Code | Meaning |
|---|---|
| `DELTA_MISMATCH` | Live head moved since the reviewed packet head. Re-review the new head. Prepended first; always BLOCKED. |
| `PINNED_CHECK_MISSING` | A pinned check never reported (absent from check runs). |
| `PINNED_CHECK_PENDING` | A pinned check reported but not `COMPLETED`. |
| `PINNED_CHECK_FAILED` | A pinned check completed non-`SUCCESS`. |
| `POLICY_UNKNOWN_REPO` | Repo not in `policies/pinned-checks.json`. Fail-closed BLOCKED. |
| `EMPTY_PIN_SET` | Known repo with an empty pin set (`autonomous-venture-company`: no CI). BLOCKED unless overridden (below). Never silently passes. |
| `OWNER_OVERRIDE_ACCEPT_RISK` | Explicit owner-accepted risk recorded on an empty pin set (with clean delta → `MERGEABLE`). Auditable, never empty. |

Pinned checks (`policies/pinned-checks.json`, D1 — `$id pinned-checks/0.3`):

- `trust-gateway`: `test`, `gate / integration`, `Analyze (javascript)`, `CodeQL`
- `aie`: `test (3.11)`, `test (3.12)`, `test (3.13)`, `Analyze (python)`, `CodeQL`
- `studio`: `Monolithic Release Verification (18 Gates)`, `Analyze (javascript)`, `CodeQL`
- `works-execution`: `test`, `Analyze (go)`, `CodeQL`
- `wi-backend`: `test (3.11)`, `test (3.12)`, `Analyze (python)`, `production-container-smoke`, `CodeQL`
- `runtime`: `build-test`
- `model-registry`: `validate`
- `autonomous-venture-company`: `[]` (empty — see override)

Cross-repo `works-execution` pending checks on AIE/WI PRs are informational,
not pinned. Dependabot / auto-merge / scorecard / brand-assets / draft
checks are not merge gates.

## Owner override label

- Name: **`OWNER_OVERRIDE_ACCEPT_RISK`** (exact).
- When: only for the empty-pin case (`autonomous-venture-company`, which
  has no `.github/workflows` and empty check rollups). It does **not**
  bypass pinned-check failures on any other repo, and it does **not**
  bypass `DELTA_MISMATCH`.
- How: apply the label to the PR, re-run the review (`workflow_dispatch`
  or push an empty commit / synchronize). The packet then carries
  `verdict: MERGEABLE` with `reason_codes: ["OWNER_OVERRIDE_ACCEPT_RISK"]`
  — explicit and auditable.
- Without the label, AVC is always `BLOCKED` with `EMPTY_PIN_SET`, even
  with zero checks reporting (an empty check list is vacuous-truth
  territory; the agent refuses the vacuous pass).

## Direct-to-main push audit (detective, non-preventive)

Job `push-audit` runs **only** on `push` to `main`. It queries
`GET repos/{owner}/{repo}/commits/<head-sha>/pulls` (read-only) and runs:

```bash
python3 scripts/audit_push.py \
  --head-sha <main-head-sha> \
  --associated-prs /tmp/associated_prs.json \
  --run-id <run-id>
```

- Head with ≥1 associated PR → JSON `verdict: AUDIT_PASS`
  (`pr_associated: true`), exit 0.
- Head with zero associated PRs (direct push) → JSON `verdict: AUDIT_FAIL`
  with a human-readable `finding`, exit 1 — **the job FAILS VISIBLY**.
  The finding JSON is appended to the packet stream
  (`docs/evidence/agent-review/<repo>-<num>-<shortsha>.json` per-PR files,
  D5) for follow-up.
- **Detective, non-preventive**: the push already landed when this runs.
  The job flags; it does not block or revert. Treat every `AUDIT_FAIL` as
  an incident: verify intent with the owner, revert if unauthorized.

## Residue risks (accepted, D3)

- **Forced pushes by an admin remain possible; flagged, not prevented.**
  Branch protection without Pro cannot block admin force-pushes; the audit
  above is the backstop. Revisit Pro if the owner asks.
- **AVC has no CI**: every AVC verdict is `BLOCKED` until a human applies
  `OWNER_OVERRIDE_ACCEPT_RISK` per PR. The override is per-PR and recorded;
  it confers no blanket approval.
- **Merge-queue packets are per-PR**: `merge_group` runs unit tests as its
  gate; the full packet verdict (delta + pins + labels) is evaluated on
  the PR event, not re-resolved inside the queue temp commit.
- **COMMENT-only**: nothing in this repo can approve, merge, or set
  statuses. If a run claims otherwise, treat the run — not this doc — as
  the bug.
- **No new identifiers / memory-authority rules** (seam-rules.json) and
  per-PR packet files (D5) are unchanged by this slice.

## Quick reference

```bash
# Unit tests (what the selftest job runs):
python3 -m unittest tests.test_agent_review tests.test_slice3 -v

# Manual review of one PR (read-only, emit-only):
python3 scripts/agent_review.py \
  --packet tests/fixtures/tg83-da5d934.json \
  --current-head <40-hex-head> \
  --checks <live-checks.json> \
  --policy policies/pinned-checks.json \
  --labels OWNER_OVERRIDE_ACCEPT_RISK

# Manual push audit (detective):
python3 scripts/audit_push.py \
  --head-sha <40-hex-main-head> \
  --associated-prs <gh-pulls-output.json>
```
