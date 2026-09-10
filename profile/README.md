<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="./assets/hero.webp">
    <img src="./assets/hero.png" alt="Aftergraph — verifiable intelligent systems" width="100%">
  </picture>
</p>

<h1 align="center">Aftergraph</h1>
<p align="center"><strong>Infrastructure and open research for verifiable intelligent systems.</strong></p>
<p align="center">Missions · Authority · Durable Execution · Evidence · Verification · Agentic Institutions</p>

Aftergraph is an engineering and research organization working on the systems layer around autonomous AI: how long-running agents can execute real work while preserving bounded authority, durable state, measurable cost, machine-verifiable evidence, and independently verified outcomes.

> **Intelligence that can act. Systems that can prove why.**
>
> 📡 **Public Knowledge Plane live:** [docs.aftergraph.org](https://docs.aftergraph.org) — architecture, contracts, claims with evidence strength, API reference, and agent-readable context packs, all provenance-stamped to exact source commits.
>
> 💬 **Public deliberation:** [Aftergraph Discussions](https://github.com/orgs/Aftergraph/discussions) — research reproduction, prior art, RFC formation, roadmap input and architecture critique.

## Start here

| If you care about… | Start with | What it contains |
|---|---|---|
| **Verifiable long-horizon agents** | [`intelligence-systems-research`](https://github.com/Aftergraph/intelligence-systems-research) | Mission Contract research, MISSION-Bench, conformance, reference runtimes, reproducibility |
| **Authority, delegation & institution semantics** | [`aie`](https://github.com/Aftergraph/aie) | Agentic Institution Engineering Draft 0.3, authority leases, revocation, budgets, evidence semantics |
| **Runtime enforcement** | [`trust-gateway`](https://github.com/Aftergraph/trust-gateway) | Trust and control boundary for governed autonomous execution |
| **Durable autonomous work** | [`works-execution`](https://github.com/Aftergraph/works-execution) | Mission execution, budgets, evidence, lifecycle and durable work primitives |
| **Work inference** | [`wi-backend`](https://github.com/Aftergraph/wi-backend) | Source-neutral observation → structured canonical WorkItem inference |
| **Cross-repo contracts & truth** | [`after-graph-governance`](https://github.com/Aftergraph/after-graph-governance) | Canonical contracts, terminology, exact-head state and claim boundaries |
| **Scheduled organization sensing** | [`aftergraph-cron-fabric`](https://github.com/Aftergraph/aftergraph-cron-fabric) | Read-only scheduled observation, evidence gating, dedupe and escalation |

**Direct public entry points:** [Discussions](https://github.com/orgs/Aftergraph/discussions) · [Public roadmap](https://github.com/Aftergraph/.github/blob/main/PUBLIC-ROADMAP.md) · [RFC process](https://github.com/Aftergraph/.github/blob/main/RFC-PROCESS.md) · [Research papers](https://github.com/Aftergraph/intelligence-systems-research/tree/main/PAPERS) · [AIE specification](https://github.com/Aftergraph/aie) · [Contributing](https://github.com/Aftergraph/.github/blob/main/CONTRIBUTING.md) · [Security](https://github.com/Aftergraph/.github/blob/main/SECURITY.md)

## What we are trying to solve

Most agent stacks are good at producing actions. Production systems need more than action generation:

```text
human intent
    ↓
mission contract
    ↓
state + capabilities + authority + budget
    ↓
execution + recovery
    ↓
evidence
    ↓
independent verification
    ↓
verified outcome
```

The core design rule is simple: **an agent saying “done” is not the same thing as the system proving the outcome.**

## Research programs

### Intelligence Systems Research

The research program investigates a vendor-neutral systems contract connecting human intent to persistent, governed and verifiable outcomes across heterogeneous models, agents, tools and runtimes.

Current public work includes:

- **SPEC-001 / Mission Contract** — machine-readable mission, state, capability, authority, budget, trajectory, evidence and verifier semantics.
- **MISSION-Bench** — fault-injected evaluation of long-horizon intelligent systems.
- **Evidence-gated completion** — `Complete ≠ Verified` as a normative system invariant.
- **Attenuated authority** — scoped, expiring and purpose-bound delegation rather than ambient credentials.
- **Cost Per Verified Outcome (CPVO)** — evaluation of useful verified work instead of raw inference price alone.
- **Cross-runtime conformance** — portable semantics rather than framework-specific governance glue.

Scientific claims remain bounded by the evidence class stated in the research repository. Deterministic sandbox results, live-provider results, simulations and external reproduction are not treated as interchangeable evidence.

### Agentic Institution Engineering (AIE)

AIE investigates the engineering layer above graph coordination and runtime control:

> **Graph defines coordination. Control enforces execution. Institution resolves legitimate authority.**

AIE focuses on portable semantics for principals, roles, authority, delegation, mission contracts, budgets, revocation, lifecycle, governed topology mutation and evidence. It is currently a **Research Draft / experimental standards track**, not a declared industry standard.

## Architecture

<p align="center"><img src="./assets/ecosystem.svg" alt="Aftergraph ecosystem" width="100%"></p>

<p align="center"><img src="./assets/architecture.svg" alt="Aftergraph operating architecture" width="100%"></p>

```text
graphs → boundaries → authority → execution → evidence → verified outcomes
```

Aftergraph intentionally composes existing standards and protocols where they already solve a problem. The goal is not to invent another transport, identity system or telemetry format merely because the industry was apparently short on acronyms.

## Public repositories

| Repository | Role |
|---|---|
| [`Aftergraph/aftergraph.org`](https://github.com/Aftergraph/aftergraph.org) | Public platform surface — landing, system launcher, health and agent index (aftergraph.org) |
| [`Aftergraph/docs`](https://github.com/Aftergraph/docs) | **Knowledge Plane** — public docs/research portal with provenance, freshness and machine-readable surfaces · live at [docs.aftergraph.org](https://docs.aftergraph.org) |
| [`Aftergraph/aie`](https://github.com/Aftergraph/aie) | Agentic Institution Engineering specification, conformance and interoperability |
| [`Aftergraph/intelligence-systems-research`](https://github.com/Aftergraph/intelligence-systems-research) | Research program, benchmark, papers, experiments and reference runtime |
| [`Aftergraph/after-graph-governance`](https://github.com/Aftergraph/after-graph-governance) | Cross-repository governance and canonical contracts |
| [`Aftergraph/trust-gateway`](https://github.com/Aftergraph/trust-gateway) | Runtime trust and enforcement surface |
| [`Aftergraph/works-execution`](https://github.com/Aftergraph/works-execution) | Durable mission execution and evidence-bearing work |
| [`Aftergraph/wi-backend`](https://github.com/Aftergraph/wi-backend) | Canonical Work Intelligence inference and WorkItem state |
| [`Aftergraph/sentinel`](https://github.com/Aftergraph/sentinel) | Exact-HEAD software verification and merge-ready verdicts |
| [`Aftergraph/aftergraph-cron-fabric`](https://github.com/Aftergraph/aftergraph-cron-fabric) | Scheduled read-only organization sensing and evidence-gated escalation |
| [`Aftergraph/studio`](https://github.com/Aftergraph/studio) | Product and operator-facing experience |
| [`Aftergraph/brand`](https://github.com/Aftergraph/brand) | Shared visual identity and public asset system |

Private, temporary, legacy-transition and incubation repositories may participate in the topology without being public entry points. Repository existence never upgrades product maturity, conformance or evidence strength.

## For researchers, implementers and reviewers

We value criticism that can falsify a claim, not merely decorate it with another opinion.

- Reproduce a benchmark or conformance result.
- Implement the specification independently.
- Test interoperability with another runtime.
- Submit contradictory prior art or a failing invariant.
- Review the threat model, evidence model or economics.
- Build against the public contracts and report semantic deviations.
- Start an `[RFC]` discussion before a cross-repository or normative change becomes implementation work.

Useful entry points: [`Discussions`](https://github.com/orgs/Aftergraph/discussions) · [`MISSION-Bench registry`](https://github.com/orgs/Aftergraph/discussions/12) · [`Prior-art challenge`](https://github.com/orgs/Aftergraph/discussions/13) · [`Architecture RFC`](https://github.com/orgs/Aftergraph/discussions/14) · [`Sentinel verdict`](https://github.com/orgs/Aftergraph/discussions/15) · [`Roadmap thread`](https://github.com/orgs/Aftergraph/discussions/16) · [`RFC intake`](https://github.com/orgs/Aftergraph/discussions/17)

## Public roadmap

Aftergraph uses gates rather than ceremonial dates. Current public priorities are independent reproduction, contract/conformance hardening, AIE candidate-readiness work, enforceable runtime boundaries, Sentinel exact-HEAD verification, and a usable public community/knowledge plane.

Read the live coordination document: [`PUBLIC-ROADMAP.md`](https://github.com/Aftergraph/.github/blob/main/PUBLIC-ROADMAP.md).

## Follow the work

⭐ **Star** the repositories you want to track.  
👀 **Watch** research and standards repositories for releases and evidence updates.  
🧪 **Reproduce** results instead of trusting screenshots, because civilization has suffered enough screenshots presented as benchmarks.  
💬 **Challenge** claims and architecture in [Discussions](https://github.com/orgs/Aftergraph/discussions) before they calcify into folklore.  
🔗 **Reference Aftergraph** when using its specifications, benchmarks or open-source implementations so downstream work remains traceable.

## Community

- [Organization Discussions](https://github.com/orgs/Aftergraph/discussions)
- [MISSION-Bench registry](https://github.com/orgs/Aftergraph/discussions/12)
- [Prior-art challenge](https://github.com/orgs/Aftergraph/discussions/13)
- [Architecture RFC](https://github.com/orgs/Aftergraph/discussions/14)
- [Sentinel verdict discussion](https://github.com/orgs/Aftergraph/discussions/15)
- [Public roadmap discussion](https://github.com/orgs/Aftergraph/discussions/16)
- [RFC intake discussion](https://github.com/orgs/Aftergraph/discussions/17)
- [Discussion routing](https://github.com/Aftergraph/.github/blob/main/DISCUSSIONS.md)
- [Public roadmap](https://github.com/Aftergraph/.github/blob/main/PUBLIC-ROADMAP.md)
- [RFC process](https://github.com/Aftergraph/.github/blob/main/RFC-PROCESS.md)
- [Contributing](https://github.com/Aftergraph/.github/blob/main/CONTRIBUTING.md)
- [Security policy](https://github.com/Aftergraph/.github/blob/main/SECURITY.md)
- [Support routing](https://github.com/Aftergraph/.github/blob/main/SUPPORT.md)
- [Code of Conduct](https://github.com/Aftergraph/.github/blob/main/CODE_OF_CONDUCT.md)

## Evidence boundaries

Runtime evidence, execution evidence, conformance evidence and scientific evidence are separate. No repository automatically inherits another repository's claims.

Canonical architecture, role allocation, contracts, naming, exact-head organization state and claim boundaries live in [`Aftergraph/after-graph-governance`](https://github.com/Aftergraph/after-graph-governance).

---

<p align="center"><strong>Open research · Responsible deployment · Verifiable progress</strong></p>

<sub>Brand status: masterbrand Aftergraph under Brand OS v1.1.0 (`Aftergraph/brand` release `v1.1.0`). Legacy “ABDE Intelligence” parent copy retired; Sentinel product identity pending naming review (`Aftergraph/brand#19`).</sub>