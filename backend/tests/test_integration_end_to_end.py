from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_should_return_full_report_contract_when_analyze_runs_with_local_documents():
    response = client.post("/analyze", json={}, headers={"x-forwarded-for": "10.0.0.11"})
    assert response.status_code == 200
    payload = response.json()["report"]

    assert payload["case_name"] == "Rivera v. Harmon Construction Group"
    assert "summary" in payload
    assert "citations" in payload
    assert "citation_verifications" in payload
    assert "quote_verifications" in payload
    assert "findings" in payload
    assert "judicial_memo" in payload
    assert "errors" in payload


def test_should_keep_summary_consistent_with_findings_counts():
    response = client.post("/analyze", json={}, headers={"x-forwarded-for": "10.0.0.12"})
    assert response.status_code == 200
    report = response.json()["report"]

    total_findings = len(report["findings"])
    high_conf = len([item for item in report["findings"] if item["confidence"] >= 0.8])
    medium_conf = len([item for item in report["findings"] if 0.5 <= item["confidence"] < 0.8])
    cnv = len([item for item in report["findings"] if item["status"] == "could_not_verify"])

    assert report["summary"]["total_findings"] == total_findings
    assert report["summary"]["high_confidence_findings"] == high_conf
    assert report["summary"]["medium_confidence_findings"] == medium_conf
    assert report["summary"]["could_not_verify"] == cnv


def test_should_extract_expected_citation_volume_and_include_statute():
    response = client.post("/analyze", json={}, headers={"x-forwarded-for": "10.0.0.13"})
    assert response.status_code == 200
    citations = response.json()["report"]["citations"]
    citations_text = [item["citation"] for item in citations]

    assert len(citations) >= 10
    assert any("California Code of Civil Procedure Section 335.1" in text for text in citations_text)


def test_should_generate_quote_verifications_for_quote_citations_only():
    response = client.post("/analyze", json={}, headers={"x-forwarded-for": "10.0.0.14"})
    assert response.status_code == 200
    report = response.json()["report"]

    quote_citation_ids = {
        item["id"] for item in report["citations"] if item["citation_type"] == "quote"
    }
    quote_verification_ids = {item["citation_id"] for item in report["quote_verifications"]}

    assert quote_verification_ids.issubset(quote_citation_ids)
    assert len(report["quote_verifications"]) >= 1


def test_should_work_with_override_documents_only_and_return_structured_payload():
    payload = {
        "use_local_documents": False,
        "documents_override": {
            "motion_for_summary_judgment": (
                "Privette v. Superior Court, 5 Cal.4th 689 (1993). "
                "\"A hirer is never liable\"."
            ),
            "police_report": "Date of Incident: March 12, 2021",
            "medical_records_excerpt": "Patient with fracture",
            "witness_statement": "Witness statement text",
        },
    }
    response = client.post("/analyze", json=payload, headers={"x-forwarded-for": "10.0.0.15"})
    assert response.status_code == 200
    report = response.json()["report"]

    assert isinstance(report["citations"], list)
    assert isinstance(report["citation_verifications"], list)
    assert isinstance(report["findings"], list)
    assert isinstance(report["judicial_memo"], str)


def test_should_keep_citation_verification_ids_linked_to_citations():
    response = client.post("/analyze", json={}, headers={"x-forwarded-for": "10.0.0.16"})
    assert response.status_code == 200
    report = response.json()["report"]
    citation_ids = {item["id"] for item in report["citations"]}
    verification_ids = {item["citation_id"] for item in report["citation_verifications"]}

    assert verification_ids.issubset(citation_ids)
    assert len(verification_ids) >= 1


def test_should_emit_allowed_status_and_confidence_ranges_in_report():
    response = client.post("/analyze", json={}, headers={"x-forwarded-for": "10.0.0.17"})
    assert response.status_code == 200
    report = response.json()["report"]

    allowed_finding_status = {"verified_issue", "could_not_verify", "no_issue"}
    allowed_quote_status = {
        "exact_match",
        "minor_difference",
        "material_omission",
        "misquote",
        "could_not_verify",
    }
    for finding in report["findings"]:
        assert finding["status"] in allowed_finding_status
        assert 0 <= finding["confidence"] <= 1
    for quote_check in report["quote_verifications"]:
        assert quote_check["status"] in allowed_quote_status
        assert 0 <= quote_check["confidence"] <= 1
