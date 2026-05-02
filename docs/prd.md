# PRD - BS Detector

## Overview and goal
Build a multi-agent pipeline to verify factual and citation reliability in a Motion for Summary Judgment, returning structured JSON for API and UI consumption.

## Scope
Includes: citation extraction, support verification, quote verification, cross-document consistency checks, confidence scoring, judicial memo generation, and evals.
Excludes: external case-law retrieval from private databases and end-user authentication.

## Functional requirements
1. Expose `POST /analyze` and return a structured report.
2. Extract citations from the motion with associated claims.
3. Verify support for each citation with status `full|partial|none|could_not_verify`.
4. Verify direct quotes and classify accuracy.
5. Verify fact consistency against police report, medical records, and witness statement.
6. Generate a short judicial memo with top findings.
7. Run evals with a single command and report precision, recall, and hallucination rate.

## Non-functional requirements
- Performance: response within up to 15s for the local document package.
- Security: no hardcoded secrets; input validation/sanitization; no sensitive logs.
- LGPD: data minimization, case-file-only usage, no PII persistence.
- Accessibility: readable UI with clear sections and labels.

## Acceptance criteria (Given/When/Then)
- Given documents in the directory, When `POST /analyze` is called, Then JSON is returned with `findings` and `summary`.
- Given a citation in the motion, When the pipeline runs, Then a corresponding item exists in `citations`.
- Given a quote without a verifiable source, When checked, Then status is `could_not_verify`.
- Given a conflicting fact between motion and police report, When cross-check runs, Then a `verified_issue` finding is returned with confidence >= 0.8.
- Given the eval gold set, When `python evals/run_evals.py` is executed, Then precision, recall, and hallucination_rate are returned.

## Risks and mitigations
- Missing source text for case law: mark as `could_not_verify` and avoid fabrication.
- Linguistic ambiguity: use short textual evidence per finding.
- Eval overfitting: keep gold set small and explicit in the repository.

## Dependencies
FastAPI, Pydantic, pytest, OpenAI SDK (optional for future evolution), Docker Compose, React/Vite.

## Definition of Done
- Functional endpoint.
- Evals runnable with a single command.
- README with setup and run instructions.
- Reflection documented.
- No hardcoded secrets.
