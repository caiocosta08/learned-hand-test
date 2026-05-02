from pathlib import Path

from app.agents.citation_extractor import CitationExtractorAgent


def test_should_extract_case_law_and_statute_citations_from_motion():
    motion = (Path(__file__).resolve().parents[1] / "documents" / "motion_for_summary_judgment.txt").read_text(encoding="utf-8")
    citations = CitationExtractorAgent().run(motion)
    has_statute = any("California Code of Civil Procedure Section 335.1" in item.citation for item in citations)
    has_privette = any("Privette v. Superior Court" in item.citation for item in citations)
    assert has_statute and has_privette


def test_should_extract_quotes_when_double_quoted_text_exists():
    motion = 'The court held "A hirer is never liable" in this context.'
    citations = CitationExtractorAgent().run(motion)
    assert any(item.citation_type == "quote" for item in citations)
