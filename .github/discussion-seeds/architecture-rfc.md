This is the cross-repository architecture review thread for Aftergraph.

The current public stack separates research/specification, institutional semantics, runtime trust enforcement, durable execution, work inference, product/operator experience, docs, and governance across multiple repositories. That separation is useful only if the boundaries remain explicit and the contracts compose cleanly.

Review the architecture as if you had to implement or operate it without access to private context.

Questions worth attacking:
- Which repository owns each canonical contract and state transition?
- Where are responsibilities duplicated or ambiguous?
- Which boundaries should be libraries, services, protocols, or simply documentation?
- What belongs in the mission/runtime path versus the evidence/verification path?
- Where could authority, budget, state, or evidence semantics diverge across repos?
- Which dependencies can be deleted rather than coordinated?
- Which cross-repo interfaces need executable conformance instead of prose?

Please cite exact files, commits, APIs, schemas, traces, or runtime behavior when possible.

Canonical organization truth: https://github.com/Aftergraph/after-graph-governance
Public architecture entry point: https://github.com/Aftergraph/.github