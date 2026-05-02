from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_should_return_report_when_analyze_called_without_payload():
    response = client.post("/analyze")
    assert response.status_code == 200


def test_should_reject_oversized_document_when_payload_exceeds_limit():
    payload = {
        "use_local_documents": False,
        "documents_override": {"motion_for_summary_judgment": "A" * 60001},
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 413


def test_should_reject_when_no_documents_are_available():
    payload = {"use_local_documents": False, "documents_override": None}
    response = client.post("/analyze", json=payload)
    assert response.status_code == 422


def test_should_reject_when_combined_payload_is_oversized():
    payload = {
        "use_local_documents": False,
        "documents_override": {
            "motion_for_summary_judgment": "A" * 50000,
            "police_report": "B" * 50000,
            "medical_records_excerpt": "C" * 50000,
            "witness_statement": "D" * 50000,
        },
    }
    response = client.post("/analyze", json=payload)
    assert response.status_code == 413


def test_should_apply_rate_limit_when_many_requests_are_sent():
    payload = {
        "use_local_documents": False,
        "documents_override": {
            "motion_for_summary_judgment": "Privette v. Superior Court, 5 Cal.4th 689 (1993).",
            "police_report": "Date of Incident: March 12, 2021",
            "medical_records_excerpt": "Fracture observed",
            "witness_statement": "Crew observed unsafe section",
        },
    }
    status_codes = []
    for _ in range(26):
        response = client.post("/analyze", json=payload, headers={"x-forwarded-for": "198.51.100.44"})
        status_codes.append(response.status_code)
    assert 429 in status_codes
