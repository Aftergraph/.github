# Aftergraph Runner Fabric v1

Status: proposed canonical organization policy.

## Goal

Make verification fast, horizontally scalable and evidence-honest without creating a second execution authority.

The fabric separates four concerns:

1. **GitHub** — trigger and status surface.
2. **Runner Fabric** — capacity, routing, clean-room materialization and queue discipline.
3. **WORKS** — durable work scheduling/pool semantics when CI moves outside GitHub Actions.
4. **Repository-native verifier** — the only component allowed to decide whether a concrete exact SHA passed its code gates.

Runner labels route work; they never grant authority.

## Fast path

For ordinary repository verification:

```
PR exact SHA
  -> shared aftergraph-ci pool
  -> one runner acquisition
  -> explicit toolchain setup
  -> repository-native checks
  -> exact-SHA receipt/status
```

No separate preflight job is permitted when the same checks can happen inside the acquired runner.

## Promotion path

Cross-repository or expensive proofs run only for promotion/manual/scheduled events:

```
promotion exact SHA
  -> aftergraph-proof/shared pool
  -> clean-room exact dependencies
  -> cross-repo proof
  -> independent evidence
```

A small edit must not enqueue the same expensive proof repeatedly.

## Queue discipline

The desired controller behavior is **latest exact SHA wins per repository/PR before execution**. An older queued SHA becomes stale; it is not a test failure and must not create a false red code signal.

Priority order:

1. hotfix
2. promotion
3. normal
4. scheduled

GitHub Actions' `cancel-in-progress` is not the canonical dedupe mechanism because cancelled workflow history is visually negative and loses the distinction between obsolete work and failed code.

## Pools

The desired common Linux pool selector is `aftergraph-ci` (with standard self-hosted/Linux/X64 labels on the registered runners). **It is not considered active organization-wide until the activation doctor and an actual `.github` job prove organization visibility.**

Repo-specific labels should be used only when the job truly requires host-specific state. Clean-room jobs should target the shared pool so additional compatible runners increase throughput automatically.

The policy contains desired warm-capacity and queue-SLO targets. Those are targets, not claims about the currently provisioned fleet.

## Isolation and cache policy

Target code executes only in an isolated workspace. Checkout credentials are not persisted. Dependency caches contain no secrets and are treated as untrusted acceleration input; verification must remain correct on a cache miss.

Public/fork PR code must not execute on a privileged persistent self-hosted machine unless a separately reviewed sandbox boundary exists.

## Relationship to existing systems

This policy does **not** replace:

- AVC/Aftergraph exact-SHA local gate isolation;
- WORKS BYOC pool/heartbeat/lease enforcement;
- AIE authority semantics;
- Trust Gateway enforcement;
- Sentinel independent verification.

It standardizes the runner/capacity layer around those existing authorities.

## 10x / 100x direction

The performance multipliers are objectives, not measured claims. The main levers are:

- one runner acquisition per gate;
- horizontal shared pools instead of repo-pinned workers;
- prewarmed toolchains on self-hosted machines;
- promotion-only expensive proofs;
- exact-ref clean-room dependency materialization;
- controller-side latest-SHA queue coalescing;
- local mirrors/package caches that never become evidence;
- WORKS-backed fleet scheduling for CI that no longer needs GitHub Actions as the execution plane;
- multiple warm runners or a runner scale set when measured queue pressure justifies it.

GitHub documents runner scale sets as the native autoscaling model through Actions Runner Controller. Adoption remains an infrastructure deployment choice, not a requirement of this v1 policy.


## Bootstrap-to-active transition

The fabric starts in `bootstrap` phase. Central control-plane selftests stay on
a known-good GitHub-hosted bootstrap runner so they cannot deadlock while the
organization pool is being created.

Activation of `aftergraph-ci` requires all three:

1. `doctor_runner_fabric_linux.sh` reports the configured warm count ready;
2. an `Aftergraph/.github` job actually runs on the `aftergraph-ci` selector;
3. exact runner names/labels are recorded as activation evidence.

Only then should `organization_visible_self_hosted_pool_proven` be changed to
`true` and central callers select `aftergraph-ci`.
