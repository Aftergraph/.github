Sentinel's core promise is stronger than "AI reviewed this pull request": a verdict should apply to the exact code state that was actually verified.

This thread is for defining the minimum evidence required before a code-review system may issue a SHIP verdict.

Candidate requirements to challenge:
- verdict bound to exact HEAD commit,
- stale base or changed HEAD invalidates prior verdict,
- cited findings resolve to the reviewed code state,
- required tests/checks are observed rather than assumed,
- fixed findings are not blindly re-reported,
- skipped or unavailable verification is explicit,
- policy and evidence used for the verdict are reconstructable,
- confidence language cannot substitute for missing evidence.

Useful counterexamples are especially welcome: cases where these guarantees are unnecessary, too expensive, impossible across common CI setups, or still insufficient to prevent unsafe merges.

Sentinel repository: https://github.com/Aftergraph/sentinel

The question is simple: what must a reviewer prove before "SHIP" means more than an optimistic comment?