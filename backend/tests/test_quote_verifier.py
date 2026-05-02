from app.agents.quote_verifier import QuoteVerifierAgent
from app.schemas.report import CitationItem


def test_should_mark_quote_as_exact_match_when_quote_exists_in_documents():
    citations = [
        CitationItem(
            id="citation_001",
            claim="x",
            citation="doc",
            quote="Date of Incident:  March 12, 2021",
            page=None,
            citation_type="quote",
        )
    ]
    docs = {"police_report": "Date of Incident:  March 12, 2021"}
    result = QuoteVerifierAgent().run(citations, docs)
    assert result[0].status == "exact_match"


def test_should_mark_quote_as_misquote_when_text_is_similar_but_wrong():
    citations = [
        CitationItem(
            id="citation_002",
            claim="x",
            citation="doc",
            quote="Date of Incident: March 14, 2021",
            page=None,
            citation_type="quote",
        )
    ]
    docs = {"police_report": "Date of Incident: March 12, 2021"}
    result = QuoteVerifierAgent().run(citations, docs)
    assert result[0].status in {"misquote", "material_omission", "minor_difference"}


def test_should_not_validate_quote_using_motion_text_as_source_of_truth():
    citations = [
        CitationItem(
            id="citation_003",
            claim="x",
            citation="motion",
            quote="A hirer is never liable",
            page=None,
            citation_type="quote",
        )
    ]
    docs = {
        "motion_for_summary_judgment": 'The court held "A hirer is never liable".',
        "police_report": "Date of Incident: March 12, 2021",
        "medical_records_excerpt": "Patient has fracture",
        "witness_statement": "Witness heard metallic snap",
    }
    result = QuoteVerifierAgent().run(citations, docs)
    assert result[0].status != "exact_match"
