# Security Policy

Aftergraph develops agent runtimes, delegated-authority systems, research prototypes and execution infrastructure. Security reports are taken seriously, especially when they concern authority escalation, credential exposure, unsafe tool execution, evidence forgery, tenant isolation, budget bypass or fail-open behavior.

## Reporting a vulnerability

Do **not** publish exploitable details in a public issue before maintainers have had a reasonable opportunity to assess the report.

Use GitHub's private vulnerability reporting / Security Advisories for the affected repository when available. If private reporting is not enabled, open a minimal public issue that states only that you need a private security contact and identifies the affected repository. Do not include secrets, exploit payloads or sensitive customer data.

A useful report contains:

- affected repository and exact commit/release;
- affected component or endpoint;
- prerequisites and threat model;
- reproducible steps or a minimal proof of concept;
- expected vs observed behavior;
- impact, including whether authority, evidence, isolation or budgets can be bypassed;
- suggested mitigation if known.

## Priority vulnerability classes

We especially want reports involving:

- privilege escalation or authority laundering;
- stale/replayed/forged authority or evidence;
- bypass of revocation, approval or kill-switch semantics;
- cross-tenant data or capability access;
- secret leakage into logs, traces, prompts or artifacts;
- unauthorized topology mutation or agent spawning;
- budget or rate-limit bypass;
- fail-open behavior where fail-closed is required;
- duplicate irreversible side effects after retries or recovery;
- tampering that is not detected by integrity mechanisms;
- supply-chain or dependency compromise affecting shipped artifacts.

## Scope and evidence boundaries

A security fix in one Aftergraph repository does not automatically establish security properties for another repository. Runtime evidence, AIE conformance evidence and scientific research evidence are separate claim classes.

Research prototypes may intentionally expose experimental interfaces. "Experimental" does not excuse avoidable secret leakage or unsafe defaults, but it does mean maintainers may choose to remove or redesign an interface rather than promise long-term compatibility.

## Safe research

Do not test against systems, accounts or data you do not own or have explicit authorization to assess. Do not exfiltrate unnecessary data. Stop once impact is demonstrated.

We value concise, reproducible vulnerability reports far more than dramatic screenshots. Computers remain stubbornly unimpressed by typography.
