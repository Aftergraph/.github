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

function fake({ prs, runs = [], behind = 0, mergeable = true, mergeableState = 'clean', children = [], files = [], comments = [], protection = 404 }) {
  const calls = [];
  const rec = (name) => async (args) => { calls.push([name, args]); return { data: {} }; };
  const github = {
    calls,
    paginate: async (fn, args) => (await fn(args)).data,
    request: async (route, args) => {
      calls.push(['request', route, args]);
      if (route.includes('/protection/required_status_checks')) {
        if (typeof protection === 'number') {
          const err = new Error(`HTTP ${protection}`);
          err.status = protection;
          throw err;
        }
        return { data: protection };
      }
      return { data: {} };
    },
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
  const github = fake({ prs: [pr(1), pr(2)], runs: green, behind: 3, protection: { strict: true } });
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

test('action_required is approved, not reported as a failure', () => {
  const latest = new Map([
    ['CI', { name: 'CI', status: 'completed', conclusion: 'action_required', id: 1 }],
    ['PR verify', { name: 'PR verify', status: 'completed', conclusion: 'success', id: 2 }],
  ]);
  const v = classify(latest, config({}));
  assert.equal(v.state, 'approve');
  assert.deepEqual(v.failed, []);
  assert.equal(v.approve.length, 1);
});

test('a real failure still wins over a run awaiting approval', () => {
  const latest = new Map([
    ['CI', { name: 'CI', status: 'completed', conclusion: 'failure', id: 1 }],
    ['PR verify', { name: 'PR verify', status: 'completed', conclusion: 'action_required', id: 2 }],
  ]);
  assert.equal(classify(latest, config({})).state, 'fail');
});

const updates = (github) => github.calls.filter(([n]) => n === 'updateBranch').length;
const merges = (github) => github.calls.filter(([n]) => n === 'merge').length;

test('behind base without strict protection: no bot update commit, the green head merges', async () => {
  for (const protection of [404, 403, { strict: false }]) {
    const github = fake({ prs: [pr(1)], runs: green, behind: 3, protection });
    const res = await run({ github, context, env: {} });
    assert.equal(updates(github), 0, `no update for protection ${JSON.stringify(protection)}`);
    assert.equal(res.action, 'merged');
    assert.equal(merges(github), 1);
  }
});

test('behind base without strict protection still waits for a missing required gate', async () => {
  const github = fake({ prs: [pr(1)], runs: [wf('CI', 'completed', 'success')], behind: 3 });
  const res = await run({ github, context, env: { STEWARD_REQUIRED: '["CI","Sentinel gate"]' } });
  assert.deepEqual(res, { action: 'waiting', number: 1 });
  assert.equal(updates(github), 0);
  assert.equal(merges(github), 0);
});

test('an unreadable protection answer falls back to updating, never to a guessed merge', async () => {
  const github = fake({ prs: [pr(1)], runs: green, behind: 2, protection: 500 });
  const res = await run({ github, context, env: {} });
  assert.deepEqual(res, { action: 'updated', number: 1 });
  assert.equal(merges(github), 0);
});

test('STEWARD_UPDATE_BRANCH always and never override the protection read', async () => {
  const always = fake({ prs: [pr(1)], runs: green, behind: 1, protection: 404 });
  assert.deepEqual(await run({ github: always, context, env: { STEWARD_UPDATE_BRANCH: 'always' } }), { action: 'updated', number: 1 });
  assert.ok(!always.calls.some(([n, route]) => n === 'request' && String(route).includes('protection')), 'always does not need to read protection');

  const never = fake({ prs: [pr(1)], runs: green, behind: 1, protection: { strict: true } });
  const res = await run({ github: never, context, env: { STEWARD_UPDATE_BRANCH: 'never' } });
  assert.equal(updates(never), 0);
  assert.equal(res.action, 'merged');
});

test('an unknown STEWARD_UPDATE_BRANCH value falls back to auto', () => {
  assert.equal(config({ STEWARD_UPDATE_BRANCH: 'sometimes' }).updateBranch, 'auto');
  assert.equal(config({}).updateBranch, 'auto');
});

test('protection is read once per pass, not once per behind PR', async () => {
  const github = fake({ prs: [pr(1), pr(2)], runs: green, behind: 1, mergeableState: 'clean', protection: 404 });
  await run({ github, context, env: {} });
  const reads = github.calls.filter(([n, route]) => n === 'request' && String(route).includes('protection')).length;
  assert.ok(reads <= 1, `read ${reads} times`);
});
