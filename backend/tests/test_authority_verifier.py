from app.agents.authority_verifier import AuthorityVerifierAgent
from app.schemas.report import CitationItem


def test_should_return_could_not_verify_when_authority_not_in_library():
    citation = CitationItem(
        id="citation_001",
        claim="Random proposition",
        citation="Unknown v. Unknown, 1 U.S. 1 (1800)",
        quote=None,
        page=None,
        citation_type="case_law",
    )
    result = AuthorityVerifierAgent().run([citation], {})
    assert result[0].support_level == "could_not_verify"


def test_should_return_partial_or_better_when_authority_in_library():
    citation = CitationItem(
        id="citation_002",
        claim="A hirer of an independent contractor is presumptively not liable for injuries arising from contracted work.",
        citation="Privette v. Superior Court, 5 Cal.4th 689 (1993)",
        quote=None,
        page=None,
        citation_type="case_law",
    )
    result = AuthorityVerifierAgent().run([citation], {})
    assert result[0].support_level in {"partial", "full"}
