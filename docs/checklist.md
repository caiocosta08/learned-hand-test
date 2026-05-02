# Implementation Checklist

## 1. SETUP
- [x] Modular structure in `backend/app` (agents, services, schemas).
- [x] Dependencies with declared versions in `requirements.txt`.
- [x] `.env.example` kept without real values.

## 2. TESTS (TDD)
- [x] Unit tests for analyzer and extractor.
- [x] Basic security tests (malicious payload and empty input).

## 3. IMPLEMENTATION
- [x] Data contracts with Pydantic.
- [x] Agents separated by responsibility.
- [x] Orchestrator service with failure handling.
- [x] `POST /analyze` endpoint.

## 4. SECURITY AND LGPD
- [x] No secrets in code.
- [x] No PII logs.
- [x] Data usage restricted to the local test package.
- [x] Findings use `could_not_verify` for uncertainty.

## 5. REVIEW
- [x] README updated with commands.
- [x] Reflection created.
- [x] Eval harness runnable with a single command.
