# Reflection

I prioritized a reliable Tier 1 delivery and the most important Tier 2 pieces over broad but fragile coverage.

## Tradeoffs
- I used deterministic agents with explicit responsibilities instead of a heavier orchestration framework.
- For case-law support validation, I return `could_not_verify` when source opinions are not present to avoid hallucinations.
- The eval harness uses a small transparent gold set, which is honest but not comprehensive.

## What I would improve with more time
- Add retrieval for cited case-law text and stronger proposition-to-holding checks.
- Expand security hardening (rate limiting middleware and stricter request schemas).
- Increase test coverage to 80%+ and add adversarial eval scenarios.
- Improve UI filtering and grouping for judge-facing workflows.
