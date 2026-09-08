# Contributing to Aftergraph

Aftergraph builds open research and infrastructure for verifiable intelligent systems. Contributions are welcome when they improve correctness, interoperability, reproducibility, security, or developer experience.

## Start with the right surface

Use an organization **Discussion** when the problem is still exploratory, cross-repository, research-oriented, or needs public critique:

https://github.com/orgs/Aftergraph/discussions

Use a repository **Issue** when the work is concrete, bounded, reproducible, and clearly owned. Use a **pull request** when you can propose the actual change with verification evidence.

For public contracts, compatibility, cross-repository semantics, governance, or new long-lived primitives, follow the organization RFC process:

https://github.com/Aftergraph/.github/blob/main/RFC-PROCESS.md

## Start in the right repository

- **Agentic Institution Engineering:** https://github.com/Aftergraph/aie
- **Intelligence Systems Research:** https://github.com/Aftergraph/intelligence-systems-research
- **Trust Gateway:** https://github.com/Aftergraph/trust-gateway
- **WORKS execution:** https://github.com/Aftergraph/works-execution
- **Work Intelligence:** https://github.com/Aftergraph/work-intelligence-v2
- **Cross-repo governance:** https://github.com/Aftergraph/after-graph-governance
- **Sentinel:** https://github.com/Aftergraph/sentinel
- **Public site:** https://github.com/Aftergraph/aftergraph.org
- **Knowledge Plane:** https://github.com/Aftergraph/docs

Each repository owns its own contracts, evidence and release claims. Do not assume a result in one repository proves a claim in another.

## What makes a strong contribution

1. State the problem or falsifiable claim clearly.
2. Reference the relevant contract, issue, study or acceptance criterion.
3. Keep changes narrow enough to review and reproduce.
4. Add or update tests for behavioral changes.
5. Record evidence for consequential runtime, conformance or research claims.
6. Prefer existing standards and protocols over inventing proprietary equivalents.
7. Separate deterministic testbed results, simulations, live-provider results and independent reproduction.
8. Record costs and tradeoffs when control, verification, policy, telemetry, or additional context is introduced.

## Research contributions

Research claims should follow the evidence discipline in `Aftergraph/intelligence-systems-research`:

- AI output is not evidence.
- Material novelty claims require documented prior-art reconnaissance.
- Confirmatory claims need a defined baseline, metrics and falsification conditions.
- Sample-bounded results must remain sample-bounded in public wording.
- Contradictory evidence is useful and should be recorded, not hidden.

Particularly valuable contributions include independent reproduction, alternative implementations, contradictory prior art, adversarial test cases and failed conformance vectors.

Useful public threads:
- MISSION-Bench reproduction registry: https://github.com/orgs/Aftergraph/discussions/12
- Prior-art challenge: https://github.com/orgs/Aftergraph/discussions/13
- Architecture RFC: https://github.com/orgs/Aftergraph/discussions/14

## Engineering contributions

Before opening a pull request:

- run the repository's documented test and lint commands;
- avoid unrelated formatting churn;
- preserve backward compatibility unless the change explicitly advances a versioned contract;
- do not weaken fail-closed behavior merely to make a test pass;
- do not add secrets, credentials, private customer data or unverifiable benchmark screenshots.

## Pull requests

A useful PR description includes:

- **Why:** problem being solved;
- **What:** behavioral or documentation change;
- **Verification:** exact commands and results;
- **Evidence boundary:** what the change proves and what it does not prove;
- **Compatibility:** affected contracts, schemas or external interfaces.

Small, evidence-bearing pull requests beat heroic mystery diffs. Humans invented the 2,000-file "tiny cleanup" PR, and reviewers have suffered enough.

## Conduct

Participate in good faith. Critique claims, mechanisms and evidence rather than people. Security reports should follow `SECURITY.md` instead of being disclosed publicly before maintainers can assess them.