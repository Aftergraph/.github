# Runner Fabric warm-pool activation

Status: implementation contract; host activation remains an operator action because GitHub registration tokens are short-lived secrets.

## Purpose

Provision 1–4 organization-scoped Linux runners that all advertise the common `aftergraph-ci` label. Workflows using:

`[self-hosted, Linux, X64, aftergraph-ci]`

can then spread across the warm pool automatically.

## Security boundary

- Bootstrap runs as root; verification jobs do not receive sudo.
- Every runner has a distinct Unix account and work directory.
- The GitHub runner archive is pinned to version `2.337.0` and a reviewed SHA-256.
- The registration token is provided only through `AFTERGRAPH_RUNNER_REGISTRATION_TOKEN`, is never written by the script, and is unset after configuration.
- Default host count is 2; the script rejects values above 4. Scale beyond that by adding hosts or a reviewed runner scale set, not by unbounded local concurrency.
- Do not expose persistent self-hosted runners to arbitrary fork code.

## Activation

Obtain a fresh **organization runner registration token** for Aftergraph, then on a reviewed Linux x64 host:

```bash
sudo -E \
  AFTERGRAPH_RUNNER_REGISTRATION_TOKEN='<short-lived-token>' \
  AFTERGRAPH_RUNNER_COUNT=2 \
  AFTERGRAPH_RUNNER_LABELS='aftergraph-ci' \
  bash scripts/bootstrap_runner_fabric_linux.sh
```

Optional:

- `AFTERGRAPH_RUNNER_GROUP`
- `AFTERGRAPH_RUNNER_ROOT`
- `AFTERGRAPH_RUNNER_NAME_PREFIX`
- `AFTERGRAPH_RUNNER_USER_PREFIX`

## Doctor

```bash
sudo AFTERGRAPH_RUNNER_COUNT=2 bash scripts/doctor_runner_fabric_linux.sh
```

The command must report `RUNNER_FABRIC_READY=2/2` before the host is counted as warm capacity.

## Capacity policy

Start with **2 runner instances** on a host only when the host has enough CPU/RAM to run two repository gates without swap pressure. Otherwise use one instance per host.

Measured pilot evidence from Rendetalje on 2026-09-20 showed queue start improving from roughly 6m15s on an overloaded serialized path to ~11s after single-acquisition/shared-pool changes. That observation is specific to those sampled runs; it is not an organization-wide SLO proof.

For sustained p95 queue time above the policy target, add another warm host or adopt a reviewed GitHub runner scale set / ARC deployment.
