# BS Detector

BS Detector is a multi-agent verification pipeline for legal briefs. It analyzes a Motion for Summary Judgment (MSJ), validates legal support and quoted text, checks factual consistency across the case file, and returns structured JSON for downstream review.

## Challenge Alignment

This repository targets the Rivera v. Harmon Construction Group case-file challenge with three tiers:

- Tier 1 (Core): citation extraction, support verification, quote checking, structured output.
- Tier 2 (Expected): eval harness, cross-document consistency checks, uncertainty handling, structured agent handoff.
- Tier 3 (Stretch): 4+ agents, confidence layer, judicial memo, resilient orchestration, readable UI, reflection.

## What Is Implemented

- `POST /analyze` endpoint returning a typed verification report.
- 6 named agents with explicit, non-overlapping responsibilities.
- Structured schema contracts via Pydantic models.
- Failure-tolerant orchestration that records stage-level errors without crashing the pipeline.
- Runnable eval harness with precision, recall, hallucination rate, adversarial checks, and dependency audit hooks.
- Frontend report UI with summary, findings, memo, and report JSON.
- Reflection document in `reflection.md`.

## Agent Pipeline

Execution order in `AnalyzerService` (`backend/app/services/analyzer.py`):

1. `CitationExtractorAgent`
2. `AuthorityVerifierAgent`
3. `QuoteVerifierAgent`
4. `FactConsistencyAgent`
5. `ConfidenceScorerAgent`
6. `JudicialMemoAgent`

Each stage passes structured data objects, not unstructured prose blobs.

## API Contract

Endpoint:

```http
POST /analyze
```

Default behavior loads local documents from `backend/documents/*.txt`.

Request body (optional):

```json
{
  "use_local_documents": true,
  "documents_override": {
    "motion_for_summary_judgment": "...",
    "police_report": "...",
    "medical_records_excerpt": "...",
    "witness_statement": "..."
  }
}
```

Response shape (see `backend/app/schemas/report.py`):

- `case_name`
- `summary`
- `citations`
- `citation_verifications`
- `quote_verifications`
- `findings`
- `judicial_memo`
- `errors`

## Setup

### Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

Services:

- API: `http://localhost:8002`
- UI: `http://localhost:5175`

### Manual Setup

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env
uvicorn main:app --reload --port 8002
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --port 5175
```

## Usage

Run analysis:

```bash
curl -X POST http://localhost:8002/analyze
```

## Evaluation Suite

Run with a single command:

```bash
cd backend
python3 evals/run_evals.py
```

Reported metrics include:

- `precision`
- `recall`
- `hallucination_rate`
- `citation_extraction_recall`
- `authority_could_not_verify_rate`
- `adversarial_passed`
- `adversarial_total`
- `pip_audit_status` and `pip_audit_issues`
- `npm_audit_status` and `npm_audit_issues`

## Tests

```bash
cd backend
python3 -m pytest
```

Coverage command:

```bash
cd backend
python3 -m pytest --cov=app --cov-report=term-missing
```

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── prompts/
│   │   ├── schemas/
│   │   └── services/
│   ├── documents/
│   ├── evals/
│   └── tests/
├── frontend/
├── docs/
└── reflection.md
```

## Known Limits

- Authority verification relies on `backend/documents/authority_library.json`; if a citation is missing, the system returns `could_not_verify`.
- Quote checks are currently bounded to supplied case-file documents and fuzzy matching heuristics.
- Eval gold/adversarial sets are intentionally small and transparent.

## Reflection

Design tradeoffs and future improvements are documented in `reflection.md`.
