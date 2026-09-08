# Aftergraph Discussions

Aftergraph Discussions is the public deliberation and research-review surface for organization-wide conversations that are not yet a scoped issue or pull request.

## Operating rule

Discussion -> evidence -> decision -> Issue/RFC -> implementation -> verification.

A discussion is not itself a canonical specification, benchmark result, release, or governance decision. Canonical truth remains in the owning repository and exact source commit.

## Active GitHub categories

Organization Discussions currently use GitHub's active default categories:

| Category | Best use |
|---|---|
| Announcements | Releases, research drops, standards milestones, material org changes |
| General | Organization-wide discussion, roadmap coordination, research registries |
| Ideas | Product/architecture ideas, prior-art challenges, RFC formation |
| Polls | Deliberative polls only; not evidence or normative decisions |
| Q&A | Questions about Aftergraph systems, research, specs and usage |
| Show and tell | Implementations, demos, reproductions and downstream work |

Structured YAML forms for additional research-specific categories are committed under `.github/DISCUSSION_TEMPLATE/`. GitHub requires the category itself to exist before a same-slug form becomes active. Until those custom categories are created in the source-repository UI, use the default routing above. The missing UI ceremony should not block useful work.

## Canonical threads

- Welcome: https://github.com/orgs/Aftergraph/discussions/9
- What comes after Graph Engineering?: https://github.com/orgs/Aftergraph/discussions/10
- SPEC-001 implementation request: https://github.com/orgs/Aftergraph/discussions/11
- MISSION-Bench reproduction registry: https://github.com/orgs/Aftergraph/discussions/12
- Prior Art Challenge: https://github.com/orgs/Aftergraph/discussions/13
- Architecture RFC: https://github.com/orgs/Aftergraph/discussions/14
- Sentinel SHIP-verdict requirements: https://github.com/orgs/Aftergraph/discussions/15
- Public Roadmap: https://github.com/orgs/Aftergraph/discussions/16
- RFC Intake: https://github.com/orgs/Aftergraph/discussions/17

## Routing

Use **Discussions** for exploration, questions, critique, reproduction reports, roadmap input, and RFC formation. Use **Issues** once the work is concrete, bounded, and actionable. Use **pull requests** for proposed repository changes. Use the owning research/spec repository for canonical evidence, conformance vectors, and normative text.

For organization-wide normative proposals, follow `RFC-PROCESS.md`.

Security vulnerabilities do not belong in public Discussions. Follow `SECURITY.md`.

## Research integrity

Aftergraph explicitly welcomes evidence that falsifies or narrows a claim. Distinguish observed fact, external evidence, synthesis, and speculation. Link exact commits/releases where possible. For reproduction work, record enough environment and method detail that another team can repeat the result.

## Moderation

Apply `CODE_OF_CONDUCT.md`. Keep disagreement technical and inspectable. Maintainers may convert mature discussions into issues/RFC work, close duplicates, or redirect repository-specific support to the owning repository.