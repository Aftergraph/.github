# Aftergraph Public Roadmap

This roadmap describes the public direction of the Aftergraph organization. It is a coordination surface, not a release promise and not a substitute for canonical repository state.

## Operating rule

Aftergraph advances claims and interfaces when evidence advances. Public work should move through:

`discussion -> evidence -> decision -> scoped issue/RFC -> implementation -> verification -> release`

Dates are intentionally secondary to gates. A repository, paper, benchmark, or specification may be useful before it is mature, but maturity labels must not outrun evidence.

## Current public priorities

### 1. Independent reproduction and falsification

**Goal:** make Aftergraph research easier to disprove, reproduce, and independently implement.

Current focus:
- independent MISSION-Bench reproductions;
- contradictory benchmark results and failure cases;
- clean-room implementations of portable contracts;
- cross-runtime conformance and semantic-deviation reporting;
- explicit separation of internal validation from third-party reproduction.

Exit evidence includes independent results, inspectable artifacts, and documented deviations rather than agreement with Aftergraph.

### 2. Mission contracts and verified outcomes

**Goal:** improve the systems contract connecting mission intent, state, capabilities, authority, budgets, trajectory, evidence, and independent verification.

The central design boundary remains `Complete != Verified`: agent self-report cannot substitute for evidence-gated outcome verification.

Priorities:
- smaller and clearer contract surfaces;
- progressive disclosure for model context efficiency;
- durable recovery without bypassing authority or budget boundaries;
- stronger evidence and verifier semantics;
- portability across heterogeneous runtimes.

### 3. Agentic Institution Engineering

**Goal:** test whether portable institution semantics add useful guarantees above graph coordination and runtime control.

AIE remains a research/experimental standards track. Candidate status is not claimed merely because a schema exists.

Priorities:
- principals, roles, authority leases, delegation and revocation;
- mission and budget conservation;
- governed topology mutation;
- stable error/event semantics;
- independent implementations and cross-runtime conformance before stronger maturity claims.

### 4. Runtime and trust surfaces

**Goal:** turn research boundaries into enforceable runtime behavior without making research text runtime authority.

Priorities:
- fail-closed authority and purpose checks;
- durable execution, pause/resume and recovery;
- measurable budget enforcement;
- reconstructable evidence trails;
- exact-head and exact-version verification where consequential decisions depend on code or contracts.

### 5. Sentinel

**Goal:** make a code-review verdict mean more than a probabilistic comment.

First wedge:
- bind a verdict to the exact reviewed HEAD;
- invalidate stale verdicts;
- cite evidence and observed checks;
- make skipped/unavailable verification explicit;
- keep the decision reconstructable.

### 6. Public knowledge and community plane

**Goal:** make it obvious where to learn, challenge, propose, reproduce, and contribute.

Priorities:
- organization Discussions as the deliberation surface;
- docs.aftergraph.org as the provenance-aware knowledge surface;
- aftergraph.org/community as the public community launcher;
- discussion forms for structured research, RFC, support and prior-art input;
- clear conversion from discussion to issue/RFC/implementation.

## Gates instead of theatre

The research progression used by Aftergraph is:

`G0 problem exists -> G1 prior-art gap -> G2 formal coherence -> G3 minimal mechanism works -> G4 material benefit -> G5 causal/ablation support -> G6 generalization -> G7 failure resilience -> G8 independent reproduction -> G9 external criticism survived`

Not every product repo uses these scientific gates verbatim, but the principle is shared: stronger public claims require stronger evidence.

## Where to participate

- Organization Discussions: https://github.com/orgs/Aftergraph/discussions
- MISSION-Bench reproduction registry: https://github.com/orgs/Aftergraph/discussions/12
- Prior-art challenge: https://github.com/orgs/Aftergraph/discussions/13
- Architecture RFC discussion: https://github.com/orgs/Aftergraph/discussions/14
- Sentinel verdict discussion: https://github.com/orgs/Aftergraph/discussions/15
- RFC process: ./RFC-PROCESS.md
- Contribution guide: ./CONTRIBUTING.md

## Status semantics

- **Research:** hypothesis, study, or experimental proposal.
- **Prototype:** implemented enough to exercise behavior; not a production guarantee.
- **Validated:** supported by the stated tests/experiments only.
- **Candidate:** interfaces and conformance are stable enough for independent implementation testing.
- **Released:** repository-defined release criteria passed.
- **Adopted:** demonstrated external use; never inferred from internal enthusiasm.

Each owning repository remains authoritative for its exact implementation state, release, evidence, and compatibility claims.