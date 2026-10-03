'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const run = require('./steward.cjs');
const { classify, latestRuns, matchesAny, config } = run;

const SHA = 'a'.repeat(40);
const OWNER = 'Aftergraph';
const REPO = 'Demo';

function wf(name, status, conclusion, extra = {}) {
  return { id: Math.floor(Math.random() * 1e9), name, event: 'pull_request', status, conclusion, created_at: '2026-10-03T20:00:00Z', run_attempt: 1, ...extra };
}

function fake({ prs, runs = [], behind = 0, mergeable = true, mergeableState = 'clean', children = [], files = [], comments = [] }) {
  const calls = [];
  const rec = (name) => async (args) => { calls.push([name, args]); return { data: {} }; };
  const github = {
    calls,
    paginate: async (fn, args) => (await fn(args)).data,
    rest: {
      repos: {
        get: async () => ({ data: { default_branch: 'main' } }),
        compareCommitsWithBasehead: async () => ({ data: { behind_by: behind } }),
      },
      pulls: {
        list: async (args) => ({ data: args.base === 'main' ? prs : children }),
        get: async ({ pull_number }) => {
          const p = prs.find((x) => x.number === pull_number);
          return { data: { ...p, state: 'open', mergeable, mergeable_state: mergeableState } };
        },
        updateBranch: rec('updateBranch'),
        update: rec('update'),
        merge: async (args) => { calls.push(['merge', args]); return { data: { sha: 'b'.repeat(40) } }; },
        listFiles: async () => ({ data: files.map((filename) => ({ filename })) }),
      },
      actions: {
        listWorkflowRunsForRepo: async () => ({ data: runs }),
        reRunWorkflowFailedJobs: rec('rerun'),
        createWorkflowDispatch: rec('dispatch'),
      },
      issues: {
        listComments: async () => ({ data: comments }),
        createComment: rec('comment'),
      },
      git: { deleteRef: rec('deleteRef') },
    },
  };
  return github;
}

function pr(number, labels = ['automerge'], extra = {}) {
  return {
    number, title: `PR ${number}`, draft: false,
    labels: labels.map((name) => ({ name })),
    head: { sha: SHA, ref: `branch-${number}`, repo: { full_name: `${OWNER}/${REPO}` } },
    ...extra,
  };
}

const context = { repo: { owner: OWNER, repo: REPO } };
const green = [wf('CI', 'completed', 'success'), wf('Sentinel gate', 'completed', 'success'), wf('CodeQL', 'completed', 'failure')];

test('merges a green, up-to-date PR with the head SHA pinned and dispatches matching workflows', async () => {
  const github = fake({ prs: [pr(7)], runs: green, files: ['apps/marketing/src/a.tsx'] });
  const env = { STEWARD_REQUIRED: '["CI","Sentinel gate"]', STEWARD_DISPATCH: JSON.stringify([{ workflow: 'marketing-deploy.yml', paths: ['apps/marketing/**'] }, { workflow: 'cloudflare-deploy.yml', paths: ['cloudflare/**'] }]) };
  const res = await run({ github, context, env });
  assert.equal(res.action, 'merged');
  const merge = github.calls.find(([n]) => n === 'merge')[1];
  assert.equal(merge.sha, SHA);
  assert.equal(merge.merge_method, 'squash');
  const dispatched = github.calls.filter(([n]) => n === 'dispatch').map(([, a]) => a.workflow_id);
  assert.deepEqual(dispatched, ['marketing-deploy.yml']);
  assert.ok(github.calls.some(([n]) => n === 'deleteRef'));
});

test('advisory failure (CodeQL) does not block, a real failure does and the queue moves on', async () => {
  const runs = [wf('CI', 'completed', 'failure')];
  const github = fake({ prs: [pr(3)], runs });
  const res = await run({ github, context, env: {} });
  assert.equal(res.action, 'idle');
  assert.ok(!github.calls.some(([n]) => n === 'merge'));
  assert.ok(github.calls.some(([n]) => n === 'comment'));
});

test('a failure is commented once per head SHA', async () => {
  const github = fake({ prs: [pr(3)], runs: [wf('CI', 'completed', 'failure')], comments: [{ body: `<!-- merge-steward:failed:${SHA} -->` }] });
  await run({ github, context, env: {} });
  assert.ok(!github.calls.some(([n]) => n === 'comment'));
});

test('behind base: updates the branch and stops (strict, serial)', async () => {
  const github = fake({ prs: [pr(1), pr(2)], runs: green, behind: 3 });
  const res = await run({ github, context, env: {} });
  assert.deepEqual(res, { action: 'updated', number: 1 });
  assert.equal(github.calls.filter(([n]) => n === 'updateBranch').length, 1);
  assert.ok(!github.calls.some(([n]) => n === 'merge'));
});

test('pending or missing required check waits at the head of the queue', async () => {
  const github = fake({ prs: [pr(1)], runs: [wf('CI', 'in_progress', null)] });
  assert.equal((await run({ github, context, env: {} })).action, 'waiting');
  const github2 = fake({ prs: [pr(1)], runs: [wf('CI', 'completed', 'success')] });
  assert.equal((await run({ github: github2, context, env: { STEWARD_REQUIRED: 'CI,Sentinel gate' } })).action, 'waiting');
});

test('cancelled run is re-run within budget, then counts as failure', async () => {
  const github = fake({ prs: [pr(1)], runs: [wf('CI', 'completed', 'cancelled')] });
  assert.equal((await run({ github, context, env: {} })).action, 'rerun');
  const github2 = fake({ prs: [pr(1)], runs: [wf('CI', 'completed', 'cancelled', { run_attempt: 3 })] });
  assert.equal((await run({ github: github2, context, env: {} })).action, 'idle');
});

test('drafts, hold labels, unlabelled PRs and forks are never merged', async () => {
  const fork = pr(4, ['automerge'], { head: { sha: SHA, ref: 'x', repo: { full_name: 'someone/Demo' } } });
  const github = fake({ prs: [pr(1, ['automerge', 'hold']), pr(2, []), pr(3, ['automerge'], { draft: true }), fork], runs: green });
  const res = await run({ github, context, env: {} });
  assert.equal(res.action, 'idle');
  assert.ok(!github.calls.some(([n]) => n === 'merge'));
});

test('conflicted PR is skipped and the next one merges', async () => {
  const github = fake({ prs: [pr(1), pr(2)], runs: green });
  const origGet = github.rest.pulls.get;
  github.rest.pulls.get = async (a) => { const r = await origGet(a); if (a.pull_number === 1) r.data.mergeable_state = 'dirty'; return r; };
  const res = await run({ github, context, env: {} });
  assert.deepEqual([res.action, res.number], ['merged', 2]);
});

test('stacked children are retargeted to the default branch before merge', async () => {
  const github = fake({ prs: [pr(1)], runs: green, children: [{ number: 9 }] });
  await run({ github, context, env: {} });
  const order = github.calls.map(([n]) => n);
  assert.ok(order.indexOf('update') > -1 && order.indexOf('update') < order.indexOf('merge'));
  assert.equal(github.calls.find(([n]) => n === 'update')[1].base, 'main');
});

test('dry run never mutates', async () => {
  const github = fake({ prs: [pr(1)], runs: green });
  const res = await run({ github, context, env: { STEWARD_DRY_RUN: 'true' } });
  assert.equal(res.action, 'would-merge');
  assert.deepEqual(github.calls, []);
});

test('helpers: latest run per name wins, push events ignored, globs', () => {
  const latest = latestRuns([
    wf('CI', 'completed', 'failure', { created_at: '2026-10-03T19:00:00Z' }),
    wf('CI', 'completed', 'success', { created_at: '2026-10-03T21:00:00Z' }),
    wf('Hosted runner probe', 'completed', 'failure', { event: 'push' }),
  ], config({}).events);
  assert.equal(latest.size, 1);
  assert.equal(classify(latest, config({})).state, 'pass');
  assert.ok(matchesAny(['apps/marketing/src/x.ts'], ['apps/marketing/**']));
  assert.ok(!matchesAny(['src/x.ts'], ['apps/marketing/**']));
  assert.ok(matchesAny(['wrangler.jsonc'], ['wrangler.jsonc']));
  assert.ok(!matchesAny(['a/wrangler.jsonc'], ['wrangler.jsonc']));
});
