# Aftergraph Discoverability Contract

This document defines the public-facing metadata and discovery vocabulary for the Aftergraph GitHub organization. Repository code and scientific evidence remain owned by their source repositories; this file only governs presentation and navigation.

## Organization positioning

**Display description**

> Infrastructure and open research for verifiable intelligent systems: missions, authority, durable execution, evidence, verification and agentic institutions.

**Primary destination**

https://github.com/Aftergraph

## Recommended pinned repositories

Pin in this order:

1. `intelligence-systems-research`
2. `aie`
3. `trust-gateway`
4. `works-execution`
5. `work-intelligence-v2`
6. `after-graph-governance`

The pin set deliberately tells one story: research → semantics → enforcement → execution → inference → governance.

## Canonical repository metadata

### `intelligence-systems-research`

**Description:** Research program for verifiable intelligent systems — SPEC-001 Mission Contracts, MISSION-Bench, assurance, replication and empirical evidence.

**Topics:** `ai-agents`, `agentic-ai`, `autonomous-agents`, `ai-evaluation`, `benchmark`, `mission-bench`, `verification`, `evidence`, `multi-agent-systems`, `ai-safety`, `reproducible-research`, `python`

### `aie`

**Description:** Agentic Institution Engineering — portable semantics for authority, delegation, revocation, budgets, lifecycle, topology governance and evidence.

**Topics:** `ai-agents`, `agentic-ai`, `multi-agent-systems`, `agent-governance`, `authorization`, `delegation`, `ai-security`, `interoperability`, `mcp`, `a2a`, `spiffe`, `conformance`

### `trust-gateway`

**Description:** Fail-closed runtime control and enforcement plane for governed autonomous agents, approvals, policy, budgets and tamper-evident audit.

**Topics:** `ai-agents`, `agent-security`, `ai-governance`, `policy-engine`, `authorization`, `audit-log`, `human-in-the-loop`, `nodejs`, `runtime-security`, `agentic-ai`

### `works-execution`

**Description:** Durable execution plane for autonomous work — missions, WorkGraph scheduling, workers, leases, budgets, recovery and execution evidence.

**Topics:** `ai-agents`, `workflow-engine`, `durable-execution`, `distributed-systems`, `scheduler`, `agentic-ai`, `verification`, `evidence`, `golang`, `automation`

### `work-intelligence-v2`

**Description:** Source-neutral work intelligence: observations become structured, attributable WorkItems for downstream autonomous systems.

**Topics:** `work-intelligence`, `ai-agents`, `agentic-ai`, `event-processing`, `observability`, `workflow`, `automation`, `structured-data`

### `after-graph-governance`

**Description:** Canonical cross-repository contracts, architecture, terminology, exact-head state and evidence boundaries for the Aftergraph ecosystem.

**Topics:** `governance`, `architecture`, `contracts`, `ai-agents`, `agentic-ai`, `interoperability`, `schemas`, `standards`, `evidence`

### `studio`

**Description:** Operator and product experience for Aftergraph systems: mission status, evidence, approvals, needs-you flows and verified outcomes.

**Topics:** `ai-agents`, `agentic-ai`, `human-in-the-loop`, `developer-tools`, `operator-console`, `mission-control`, `ux`

### `brand`

**Description:** Aftergraph Brand OS and design system: identity, tokens, canonical assets and public communication contracts.

**Topics:** `design-system`, `branding`, `design-tokens`, `svg`, `accessibility`, `developer-tools`

## Repository front-door rules

Every public repository SHOULD expose these within the first screen or first major sections of its README:

1. one-sentence purpose;
2. current maturity/status without inflated claims;
3. 5-minute or shortest viable quickstart;
4. architecture or workflow visual where useful;
5. evidence/verification boundary;
6. link back to `https://github.com/Aftergraph`;
7. contribution/security path;
8. citation metadata for research/specification repositories.

## Search vocabulary

Use naturally in README prose, documentation titles and release descriptions when actually relevant:

`verifiable intelligent systems`, `long-horizon agents`, `autonomous agents`, `agentic AI`, `mission contracts`, `AI agent verification`, `evidence-gated agents`, `delegated authority`, `agent governance`, `agent security`, `multi-agent systems`, `MCP`, `A2A`, `SPIFFE`, `OpenTelemetry`, `fault injection`, `MISSION-Bench`, `Agentic Institution Engineering`.

Do not dump keywords into prose where they make no semantic sense. Search engines, unlike certain pitch decks, eventually notice.

## Community surfaces

Enable or maintain where repository maturity warrants it:

- Issues for bugs, interoperability and reproducibility reports;
- Discussions for broad design questions on `aie` and `intelligence-systems-research` when moderation capacity exists;
- Security Advisories / private vulnerability reporting on security-sensitive repositories;
- Releases for externally meaningful specification, benchmark and software milestones;
- `CITATION.cff` for research/specification repositories.

## Release naming

Prefer human-readable release titles that expose the artifact and maturity, for example:

- `AIE Draft 0.3 — Candidate-readiness semantics`
- `SPEC-001 Mission Contract v0.1 — Research snapshot`
- `MISSION-Bench — deterministic benchmark dataset snapshot`

Never title an internally validated research snapshot as an industry standard.

## Public evidence law

Marketing and metadata MUST NOT silently upgrade:

- simulation → live evidence;
- internal conformance → external reproduction;
- zero observed failures → zero population risk;
- research draft → established standard;
- provisional brand → trademark-cleared identity.

Visibility is useful. Fiction with good SEO is still fiction.
