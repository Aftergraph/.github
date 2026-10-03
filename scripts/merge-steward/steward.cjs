'use strict';
/**
 * Merge steward: a serial, label-driven merge queue for repositories where
 * GitHub's own auto-merge and merge queue cannot gate anything.
 *
 * Why it exists: Aftergraph is on GitHub Free, so private repositories have no
 * branch protection, rulesets, required checks or merge queue. Native
 * auto-merge only waits on required checks, so without them it is either
 * unavailable or merges immediately. The steward is the gate instead.
 *
 * One pass does at most ONE mutating step and then stops, so the queue stays
 * strictly serial:
 *   1. Candidates: open, non-draft PRs into the default branch that carry the
 *      queue label and none of the hold labels, from this repository (never a
 *      fork), oldest PR number first.
 *   2. Conflicted or failed PRs are reported once per head SHA and skipped;
 *      they do not block the queue.
 *   3. A PR behind the default branch is updated (merge of base into head) and
 *      the pass stops: its checks must re-run against the current base. This is
 *      the "strict, up to date" guarantee a merge queue would give.
 *   4. A cancelled run on the head SHA is re-run (bounded by maxReruns); the
 *      pass stops while it runs.
 *   5. A green, up-to-date PR is merged with the head SHA pinned. Stacked
 *      children are retargeted to the default branch first, so deleting the
 *      head branch cannot auto-close them.
 *   6. Merges made with GITHUB_TOKEN do not fire push workflows, so the
 *      configured post-merge workflows are dispatched explicitly, filtered by
 *      the files the PR changed.
 *
 * Checks are read from workflow runs on the head SHA (pull_request and
 * pull_request_target events), latest run per workflow name. Every such
 * workflow must pass unless it is advisory; required names must also exist.
 */

const PASS = new Set(['success', 'skipped', 'neutral']);
const MARKER = 'merge-steward';

function list(value, fallback = []) {
  if (value === undefined || value === null || value === '') return fallback;
  if (Array.isArray(value)) return value;
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed : fallback;
  } catch {
    return String(value).split(',').map((s) => s.trim()).filter(Boolean);
  }
}

function config(env) {
  return {
    label: env.STEWARD_LABEL || 'automerge',
    holdLabels: list(env.STEWARD_HOLD_LABELS, ['hold', 'do-not-merge', 'wip']),
    required: list(env.STEWARD_REQUIRED, []),
    advisory: list(env.STEWARD_ADVISORY, ['CodeQL', 'OpenSSF Scorecard', 'Auto-merge Dependabot', 'Merge steward']),
    dispatch: list(env.STEWARD_DISPATCH, []),
    mergeMethod: env.STEWARD_MERGE_METHOD || 'squash',
    dryRun: String(env.STEWARD_DRY_RUN || 'false') === 'true',
    maxReruns: Number.parseInt(env.STEWARD_MAX_RERUNS || '2', 10),
    events: list(env.STEWARD_EVENTS, ['pull_request', 'pull_request_target']),
  };
}

/** Minimal glob: `**` spans directories, `*` stays within one segment. */
function globToRegExp(glob) {
  let re = '';
  for (let i = 0; i < glob.length; i += 1) {
    const c = glob[i];
    if (c === '*' && glob[i + 1] === '*') {
      re += '.*';
      i += 1;
      if (glob[i + 1] === '/') i += 1;
    } else if (c === '*') {
      re += '[^/]*';
    } else if (c === '?') {
      re += '[^/]';
    } else {
      re += c.replace(/[.+^${}()|[\]\\]/g, '\\$&');
    }
  }
  return new RegExp(`^${re}$`);
}

function matchesAny(files, globs) {
  if (!globs || globs.length === 0) return true;
  const res = globs.map(globToRegExp);
  return files.some((f) => res.some((r) => r.test(f)));
}

/** Latest run per workflow name, PR events only. */
function latestRuns(runs, events) {
  const latest = new Map();
  for (const run of runs) {
    if (!events.includes(run.event)) continue;
    const prev = latest.get(run.name);
    const newer = !prev
      || Date.parse(run.created_at) > Date.parse(prev.created_at)
      || (run.created_at === prev.created_at && (run.run_attempt || 1) > (prev.run_attempt || 1));
    if (newer) latest.set(run.name, run);
  }
  return latest;
}

/**
 * Classify the head SHA's checks.
 * @returns {{state: 'pass'|'pending'|'fail'|'rerun', pending: string[], failed: string[], rerun: object[], missing: string[]}}
 */
function classify(latest, cfg) {
  const pending = [];
  const failed = [];
  const rerun = [];
  for (const [name, run] of latest) {
    if (cfg.advisory.includes(name)) continue;
    if (run.status !== 'completed') {
      pending.push(name);
    } else if (run.conclusion === 'cancelled' && (run.run_attempt || 1) <= cfg.maxReruns) {
      rerun.push(run);
    } else if (!PASS.has(run.conclusion)) {
      failed.push(`${name} (${run.conclusion})`);
    }
  }
  const missing = cfg.required.filter((name) => !latest.has(name));
  let state = 'pass';
  if (failed.length) state = 'fail';
  else if (rerun.length) state = 'rerun';
  else if (pending.length || missing.length) state = 'pending';
  else if (latest.size === 0) state = 'pending';
  return { state, pending, failed, rerun, missing };
}

async function alreadyNoted(github, owner, repo, number, tag) {
  const comments = await github.paginate(github.rest.issues.listComments, {
    owner, repo, issue_number: number, per_page: 100,
  });
  return comments.some((c) => (c.body || '').includes(tag));
}

async function note(ctx, pr, kind, text) {
  const { github, owner, repo, cfg, log } = ctx;
  const tag = `<!-- ${MARKER}:${kind}:${pr.head.sha} -->`;
  log(`#${pr.number} ${kind}: ${text}`);
  if (cfg.dryRun) return;
  if (await alreadyNoted(github, owner, repo, pr.number, tag)) return;
  await github.rest.issues.createComment({
    owner, repo, issue_number: pr.number,
    body: `${tag}\n**Merge steward:** ${text}\n\nHead \`${pr.head.sha.slice(0, 7)}\`. Push a fix or re-run the checks and the queue picks it up again; remove the \`${cfg.label}\` label to take it out of the queue.`,
  });
}

async function run({ github, context, core, env = process.env }) {
  const cfg = config(env);
  const { owner, repo } = context.repo;
  const lines = [];
  const log = (s) => { lines.push(s); if (core) core.info(s); };
  const ctx = { github, owner, repo, cfg, log };

  const { data: repoInfo } = await github.rest.repos.get({ owner, repo });
  const base = repoInfo.default_branch;

  const open = await github.paginate(github.rest.pulls.list, {
    owner, repo, state: 'open', base, per_page: 100,
  });
  const queue = open
    .filter((p) => !p.draft)
    .filter((p) => p.labels.some((l) => l.name === cfg.label))
    .filter((p) => !p.labels.some((l) => cfg.holdLabels.includes(l.name)))
    .sort((a, b) => a.number - b.number);

  log(`queue (${cfg.label}) on ${owner}/${repo}@${base}: ${queue.map((p) => `#${p.number}`).join(', ') || 'empty'}${cfg.dryRun ? ' [dry run]' : ''}`);

  let result = { action: 'idle' };
  for (const item of queue) {
    const { data: pr } = await github.rest.pulls.get({ owner, repo, pull_number: item.number });
    if (pr.state !== 'open' || pr.draft) continue;
    if (!pr.head.repo || pr.head.repo.full_name !== `${owner}/${repo}`) {
      log(`#${pr.number} skipped: head is a fork, never merged by the steward`);
      continue;
    }
    if (pr.mergeable_state === 'dirty') {
      await note(ctx, pr, 'conflict', `merge conflict with \`${base}\`. It needs a rebase before it can be queued.`);
      continue;
    }

    const { data: cmp } = await github.rest.repos.compareCommitsWithBasehead({
      owner, repo, basehead: `${base}...${pr.head.sha}`,
    });
    if (cmp.behind_by > 0) {
      log(`#${pr.number} is ${cmp.behind_by} behind ${base}: updating branch so checks run on the current base`);
      if (!cfg.dryRun) {
        await github.rest.pulls.updateBranch({ owner, repo, pull_number: pr.number, expected_head_sha: pr.head.sha });
      }
      result = { action: 'updated', number: pr.number };
      break;
    }

    const runs = await github.paginate(github.rest.actions.listWorkflowRunsForRepo, {
      owner, repo, head_sha: pr.head.sha, per_page: 100,
    });
    const verdict = classify(latestRuns(runs, cfg.events), cfg);

    if (verdict.state === 'fail') {
      await note(ctx, pr, 'failed', `not merged, these checks failed: ${verdict.failed.join(', ')}.`);
      continue;
    }
    if (verdict.state === 'rerun') {
      for (const r of verdict.rerun) {
        log(`#${pr.number} re-running cancelled "${r.name}" (attempt ${r.run_attempt || 1})`);
        if (!cfg.dryRun) {
          await github.rest.actions.reRunWorkflowFailedJobs({ owner, repo, run_id: r.id });
        }
      }
      result = { action: 'rerun', number: pr.number };
      break;
    }
    if (verdict.state === 'pending') {
      const why = [...verdict.pending.map((n) => `${n} running`), ...verdict.missing.map((n) => `${n} not reported`)];
      log(`#${pr.number} waiting: ${why.join(', ') || 'no checks reported yet'}`);
      result = { action: 'waiting', number: pr.number };
      break;
    }
    if (pr.mergeable === null) {
      log(`#${pr.number} waiting: GitHub is still computing mergeability`);
      result = { action: 'waiting', number: pr.number };
      break;
    }
    if (pr.mergeable === false) {
      await note(ctx, pr, 'conflict', `GitHub reports it as not mergeable into \`${base}\`.`);
      continue;
    }

    const children = await github.paginate(github.rest.pulls.list, {
      owner, repo, state: 'open', base: pr.head.ref, per_page: 100,
    });
    for (const child of children) {
      log(`#${pr.number} retargeting stacked #${child.number} to ${base} before merge`);
      if (!cfg.dryRun) {
        await github.rest.pulls.update({ owner, repo, pull_number: child.number, base });
      }
    }

    log(`#${pr.number} green and up to date: merging (${cfg.mergeMethod}) at ${pr.head.sha.slice(0, 7)}`);
    if (cfg.dryRun) {
      result = { action: 'would-merge', number: pr.number };
      break;
    }
    const { data: merged } = await github.rest.pulls.merge({
      owner, repo, pull_number: pr.number, sha: pr.head.sha,
      merge_method: cfg.mergeMethod, commit_title: `${pr.title} (#${pr.number})`,
    });
    log(`#${pr.number} merged as ${merged.sha}`);

    try {
      await github.rest.git.deleteRef({ owner, repo, ref: `heads/${pr.head.ref}` });
    } catch (err) {
      log(`#${pr.number} branch ${pr.head.ref} not deleted: ${err.message}`);
    }

    const files = (await github.paginate(github.rest.pulls.listFiles, {
      owner, repo, pull_number: pr.number, per_page: 100,
    })).map((f) => f.filename);
    const dispatched = [];
    for (const d of cfg.dispatch) {
      const spec = typeof d === 'string' ? { workflow: d } : d;
      if (!matchesAny(files, spec.paths)) continue;
      try {
        await github.rest.actions.createWorkflowDispatch({
          owner, repo, workflow_id: spec.workflow, ref: base, inputs: spec.inputs || {},
        });
        dispatched.push(spec.workflow);
      } catch (err) {
        log(`dispatch ${spec.workflow} failed: ${err.message}`);
      }
    }
    if (dispatched.length) log(`dispatched on ${base}: ${dispatched.join(', ')}`);

    await github.rest.issues.createComment({
      owner, repo, issue_number: pr.number,
      body: `<!-- ${MARKER}:merged:${pr.head.sha} -->\n**Merge steward:** merged as ${merged.sha} after every check passed on \`${pr.head.sha.slice(0, 7)}\` against current \`${base}\`.${dispatched.length ? ` Post-merge: ${dispatched.map((w) => `\`${w}\``).join(', ')}.` : ''}`,
    });
    result = { action: 'merged', number: pr.number, sha: merged.sha, dispatched };
    break;
  }

  if (core && core.summary) {
    await core.summary.addHeading('Merge steward', 3).addCodeBlock(lines.join('\n')).write();
  }
  return result;
}

module.exports = run;
module.exports.run = run;
module.exports.config = config;
module.exports.classify = classify;
module.exports.latestRuns = latestRuns;
module.exports.globToRegExp = globToRegExp;
module.exports.matchesAny = matchesAny;
