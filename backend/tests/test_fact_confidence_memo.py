from pathlib import Path

from app.agents.confidence_scorer import ConfidenceScorerAgent
from app.agents.fact_consistency import FactConsistencyAgent
from app.agents.judicial_memo import JudicialMemoAgent
from app.services.document_loader import DocumentLoader


def test_should_return_findings_when_documents_are_present():
    docs = DocumentLoader(Path(__file__).resolve().parents[1] / "documents").load_documents()
    findings = FactConsistencyAgent().run(docs)
    assert len(findings) >= 3


def test_should_keep_confidence_in_range_after_scoring():
    docs = DocumentLoader(Path(__file__).resolve().parents[1] / "documents").load_documents()
    findings = FactConsistencyAgent().run(docs)
    scored = ConfidenceScorerAgent().run(findings)
    assert all(0 <= item.confidence <= 1 for item in scored)


def test_should_generate_judicial_memo_from_verified_issues():
    docs = DocumentLoader(Path(__file__).resolve().parents[1] / "documents").load_documents()
    findings = FactConsistencyAgent().run(docs)
    memo = JudicialMemoAgent().run(findings)
    assert isinstance(memo, str) and len(memo) > 20
