# Aftergraph Public Profile Audit

**Date:** 2026-09-06  
**Scope:** public GitHub discoverability surfaces  
**Canonical metadata:** [`DISCOVERABILITY.md`](./DISCOVERABILITY.md)

This audit records what is already implemented in repository content and what still depends on GitHub repository/organization settings.

## Completed content-level work

- organization profile front door rewritten around **verifiable intelligent systems**;
- flagship repository routing added;
- public research paper index added;
- `CITATION.cff` added to Intelligence Systems Research;
- AIE citation URL corrected to `https://github.com/Aftergraph/aie`;
- organization-wide contribution, security, support and conduct files added;
- organization-wide PR and issue templates added;
- public launch kit added to `Aftergraph/brand`;
- public distribution plan added to `Aftergraph/brand`;
- AIE public release evidence gate added;
- Intelligence Systems Research public release evidence gate added;
- canonical descriptions/topics/pinning order frozen in `DISCOVERABILITY.md`.

## Verified GitHub-setting gaps

At the time of this audit, repository metadata reads showed:

### `Aftergraph/aie`

- description already useful;
- `topics: []`;
- `homepage: null`;
- `has_discussions: false`.

### `Aftergraph/intelligence-systems-research`

- description already useful;
- `topics: []`;
- `homepage: null`;
- `has_discussions: false`.

### `Aftergraph/trust-gateway`

- description already useful;
- `topics: []`;
- `homepage: null`;
- `has_discussions: false`.

### `Aftergraph/works-execution`

- description already useful;
- `topics: []`;
- `homepage: null`;
- `has_discussions: false`.

### `Aftergraph/after-graph-governance`

- `topics: []`;
- `has_discussions: false`;
- stale homepage points to `https://github.com/JonasAbde` and should be replaced or cleared.

### `Aftergraph/brand`

- description exists;
- `topics: []`;
- `homepage: null`;
- `has_discussions: false`.

## Admin operations still required

The connected GitHub App used for this wave has repository content/issues/PR/workflow permissions, but the exposed connector does not provide repository-settings mutations for these fields. Therefore the following are not represented as completed:

1. apply canonical topics from `DISCOVERABILITY.md`;
2. set/clean canonical homepages;
3. set organization description/website if not already configured in GitHub settings;
4. pin flagship repositories in the canonical order;
5. enable Discussions for AIE / Research if approved;
6. verify/enable private vulnerability reporting for security-sensitive repositories;
7. publish externally meaningful GitHub Releases through an authorized release/settings surface.

These are tracked in issue #6.

## Pin order

1. `intelligence-systems-research`
2. `aie`
3. `trust-gateway`
4. `works-execution`
5. `work-intelligence-v2`
6. `after-graph-governance`

## Public story

`Research → Institution Semantics → Enforcement → Execution → Intelligence → Governance`

This ordering should remain stable unless the actual architecture changes. Random pin rotation because a repository had an exciting Tuesday is not information architecture.
