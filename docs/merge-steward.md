# Merge steward

A serial, label-driven merge queue for Aftergraph repositories.

## Why not GitHub auto-merge

Aftergraph is on GitHub Free. On a private repository that means no branch
protection, no rulesets, no required checks and no merge queue (the API answers
"Upgrade to GitHub Pro"). GitHub's native auto-merge only waits for required
checks, so without them it has nothing to wait for. The merge queue is only
available on public repositories or on GitHub Enterprise Cloud.

The steward is therefore the gate itself, run from Actions on our own runners.

## What one pass does

1. Takes open, non-draft PRs into the default branch that carry `automerge` and
   none of `hold`, `do-not-merge`, `wip`. Forks are never merged. Oldest first.
2. Skips a conflicted or failed PR with one comment per head SHA. It does not
   block the queue.
3. When a PR is behind the default branch, updates it and stops only if the
   base requires up-to-date branches (`update_branch: auto`, the default) or
   the caller sets `update_branch: always`. Otherwise the checks on the head
   stand and the squash merge lands on the current base. The update commit is
   authored by `github-actions[bot]`, and GitHub fires no
   `pull_request_target` workflow for it, so a required gate on that event
   (Sentinel) would never report and the PR would wait forever. On GitHub Free
   private repos the protection read returns 403, which counts as "not
   required". Any other unreadable answer falls back to updating.
4. Re-runs a cancelled workflow run (up to `max_reruns` attempts) and stops.
5. Merges a green, up-to-date PR with the head SHA pinned. Stacked PRs based on
   its branch are retargeted to the default branch first, so deleting the
   branch cannot auto-close them.
6. Dispatches the configured post-merge workflows, filtered by changed paths.
   A merge made with `GITHUB_TOKEN` does not fire `push` workflows, so deploys
   that normally run on push to `main` need a `workflow_dispatch` trigger and an
   entry in `dispatch`.

"Green" means: the latest run of every workflow on the head SHA from a
`pull_request` or `pull_request_target` event passed (success, skipped or
neutral), except workflows listed as `advisory`, and every name in `required`
is present.

## Onboarding a repository

Add `.github/workflows/merge-steward.yml`:

```yaml
name: Merge steward
on:
  workflow_run:
    workflows: [CI, Sentinel gate]   # the PR workflows that decide a merge
    types: [completed]
  pull_request_target:
    types: [labeled, ready_for_review]
  schedule:
    - cron: '*/20 * * * *'
  workflow_dispatch:
    inputs:
      dry_run: { type: boolean, default: false }
concurrency:
  group: merge-steward
  cancel-in-progress: false
permissions:
  contents: write
  pull-requests: write
  issues: write
  actions: write
  checks: read
jobs:
  steward:
    if: github.event_name != 'pull_request_target' || github.event.label.name == 'automerge' || github.event.action == 'ready_for_review'
    uses: Aftergraph/.github/.github/workflows/merge-steward.yml@<sha>
    with:
      engine_ref: <sha>
      runs_on: '["self-hosted","Linux","X64"]'
      required: '["CI","Sentinel gate"]'
      dispatch: '[{"workflow":"deploy.yml","paths":["src/**"]}]'
```

Then create the `automerge` label and put it on a PR. Start with
`dry_run: true` from the Actions tab to read what it would do.

## Safety properties

- Never merges a draft, a fork, a held PR, or a PR whose head moved after
  evaluation (the merge call pins the head SHA).
- Never merges a PR that is behind the base branch when the base requires
  up-to-date branches, or when `update_branch: always` is set.
- Never merges on a failed, missing or running required check.
- Never touches workflow code from the PR: it does not check out PR code.
- One mutating step per pass, serialized by the caller's concurrency group.

## Upgrade path

With a GitHub App token instead of `GITHUB_TOKEN`, merges fire `push` workflows
normally and `dispatch` becomes unnecessary. If the org moves to a paid plan,
native required checks plus GitHub's merge queue can replace the steward.
