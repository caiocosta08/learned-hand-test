from pathlib import Path

from app.services.analyzer import AnalyzerService
from app.services.document_loader import DocumentLoader


def test_should_return_structured_report_when_documents_loaded():
    loader = DocumentLoader(Path(__file__).resolve().parents[1] / "documents")
    documents = loader.load_documents()

    report = AnalyzerService().analyze(documents)

    assert report.case_name == "Rivera v. Harmon Construction Group"


def test_should_flag_date_conflict_when_motion_differs_from_police_report():
    loader = DocumentLoader(Path(__file__).resolve().parents[1] / "documents")
    documents = loader.load_documents()

    report = AnalyzerService().analyze(documents)

    assert any(item.type == "cross_document_date_conflict" for item in report.findings)
