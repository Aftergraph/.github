# Aftergraph Discussions

Aftergraph Discussions is the public deliberation and research-review surface for organization-wide conversations that are not yet a scoped issue or pull request.

## Operating rule

Discussion -> evidence -> decision -> Issue/RFC -> implementation -> verification.

A discussion is not itself a canonical specification, benchmark result, release, or governance decision. Canonical truth remains in the owning repository and exact source commit.

## Categories

| Category | Format | Purpose |
|---|---|---|
| Announcements | Announcement | Releases, research drops, standards milestones, material org changes |
| General | Open-ended | Organization-wide conversation |
| Ideas | Open-ended | Early product, architecture, research, and ecosystem ideas |
| Q&A | Question/answer | Questions about Aftergraph systems, research, specs, and usage |
| Show and tell | Open-ended | Implementations, demos, reproductions, and downstream work |
| Research and Reproduction | Open-ended | MISSION-Bench, conformance, independent implementation, contradictory results |
| Specifications and RFCs | Open-ended | Proposed changes to contracts, schemas, invariants, registries, and governance |
| Prior Art and Critique | Open-ended | Papers, patents, source code, standards, product behavior, falsification |
| Help and Integrations | Question/answer | Runtime, protocol, SDK, deployment, and integration support |

The YAML files under `.github/DISCUSSION_TEMPLATE/` are category forms. GitHub requires each filename to match the category slug. Default categories use GitHub's default slugs. Custom categories should be created with names that resolve to the committed slugs.

## Routing

Use **Discussions** for exploration, questions, critique, reproduction reports, and RFC formation. Use **Issues** once the work is concrete, bounded, and actionable. Use **pull requests** for proposed repository changes. Use the owning research/spec repository for canonical evidence, conformance vectors, and normative text.

Security vulnerabilities do not belong in public Discussions. Follow `SECURITY.md`.

## Research integrity

Aftergraph explicitly welcomes evidence that falsifies or narrows a claim. Distinguish observed fact, external evidence, synthesis, and speculation. Link exact commits/releases where possible. For reproduction work, record enough environment and method detail that another team can repeat the result.

## Moderation

Apply `CODE_OF_CONDUCT.md`. Keep disagreement technical and inspectable. Maintainers may convert mature discussions into issues/RFC work, close duplicates, or redirect repository-specific support to the owning repository.
