from app.agents.citation_extractor import CitationExtractorAgent


def test_should_not_crash_when_input_contains_sql_injection_payload():
    motion = "Claim text ' OR 1=1; DROP TABLE cases; -- Privette v. Superior Court, 5 Cal.4th 689 (1993)."
    result = CitationExtractorAgent().run(motion)
    assert isinstance(result, list)


def test_should_return_empty_list_when_input_is_null_equivalent():
    result = CitationExtractorAgent().run("")
    assert result == []
