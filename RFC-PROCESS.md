# Aftergraph RFC Process

The RFC process is for changes whose blast radius is larger than one obvious implementation task: public contracts, cross-repository behavior, compatibility boundaries, normative semantics, governance, or new long-lived primitives.

An RFC is not required for every bug fix. Humanity already has enough process documents attempting to supervise punctuation.

## Start with a Discussion

Open an organization Discussion in **Ideas**:

https://github.com/orgs/Aftergraph/discussions/new?category=ideas

Use a title beginning with `[RFC]` for proposals intended to become normative or cross-repository decisions.

Before the proposal becomes an implementation issue, the discussion should establish:

1. **Problem** — concrete failure, user need, research gap, or compatibility problem.
2. **Scope** — repositories, contracts, runtimes, users, and interfaces affected.
3. **Evidence** — measurements, incidents, research, standards, user evidence, or reproducible behavior.
4. **Prior art / alternatives** — existing standards, products, source code, simpler mechanisms, and the option to do nothing.
5. **Proposed semantics** — the smallest behavioral change that solves the problem.
6. **Compatibility** — schema, behavior, migration, deprecation, and extension impact.
7. **Security / authority impact** — how privilege, delegation, revocation, trust, or fail-closed behavior changes.
8. **Economics** — token, latency, compute, storage, integration, and human-attention cost where relevant.
9. **Verification** — how an independent implementation or test can determine conformance.
10. **Falsifiers** — evidence that would narrow, reject, or reverse the proposal.

## Lifecycle

```text
DRAFT DISCUSSION
      |
      v
EVIDENCE / PRIOR ART
      |
      v
OWNER + SCOPE RESOLVED
      |
      v
RFC / ISSUE IN OWNING REPOSITORY
      |
      v
REFERENCE IMPLEMENTATION
      |
      v
CONFORMANCE / INTEROP / MIGRATION TESTS
      |
      v
DECISION + VERSIONED RELEASE
```

### 1. Discussion

The community can challenge the problem statement, find existing solutions, expose hidden costs, and identify the correct owning repository.

### 2. Evidence packet

Claims must be labelled by evidence strength. AI-generated prose, popularity, or maintainer confidence is not evidence.

For research-affecting proposals, record contradictory evidence and preserve sample-bounded wording.

### 3. Ownership decision

One repository must own normative truth. Cross-repository consumers reference that source rather than copying a competing definition.

### 4. RFC or scoped issue

Once the semantics are clear enough to implement, open the actionable work in the owning repository and link back to the Discussion.

### 5. Implementation and conformance

Normative behavior should have executable tests or vectors where practical. A reference implementation is useful, but it is not independent reproduction.

### 6. Decision

Record:
- accepted/rejected/narrowed status;
- exact version or commit;
- compatibility implications;
- evidence used;
- unresolved objections;
- migration/deprecation plan where needed.

## When an RFC must not silently ship

Escalate rather than direct-merge when a change:
- expands authority or delegation;
- weakens fail-closed behavior;
- changes evidence/verification semantics;
- breaks a public schema or protocol binding;
- changes mission, lifecycle, budget, or topology invariants;
- creates a new cross-repository source of truth;
- upgrades a research claim or maturity label.

## Research integrity boundary

Aftergraph's research protocol requires novelty and material claims to survive literature, standards, source-code, patent, and product reconnaissance before strong novelty classifications advance. Confirmatory studies should define baselines, metrics, statistical plan, success thresholds, and falsification conditions before execution.

## Fast path

A proposal may skip a long RFC discussion when all of the following are true:
- behavior is already specified by an owning canonical contract;
- compatibility is unchanged;
- authority/safety/evidence boundaries are unchanged;
- tests make correctness obvious;
- the change is narrow and reversible.

Fast does not mean undocumented. The PR still carries verification evidence.