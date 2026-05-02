from __future__ import annotations

from app.agents.authority_verifier import AuthorityVerifierAgent
from app.agents.citation_extractor import CitationExtractorAgent
from app.agents.confidence_scorer import ConfidenceScorerAgent
from app.agents.fact_consistency import FactConsistencyAgent
from app.agents.judicial_memo import JudicialMemoAgent
from app.agents.quote_verifier import QuoteVerifierAgent
from app.schemas.report import ReportSummary, VerificationReport


class AnalyzerService:
    def __init__(self):
        self.citation_extractor = CitationExtractorAgent()
        self.authority_verifier = AuthorityVerifierAgent()
        self.quote_verifier = QuoteVerifierAgent()
        self.fact_consistency = FactConsistencyAgent()
        self.confidence_scorer = ConfidenceScorerAgent()
        self.judicial_memo = JudicialMemoAgent()

    def analyze(self, documents: dict[str, str]) -> VerificationReport:
        errors: list[str] = []
        motion = documents.get("motion_for_summary_judgment", "")
        citations = self.citation_extractor.run(motion)

        try:
            citation_checks = self.authority_verifier.run(citations, documents)
        except Exception as exc:  # pragma: no cover
            citation_checks = []
            errors.append(f"authority_verifier_failed: {exc}")

        try:
            quote_checks = self.quote_verifier.run(citations, documents)
        except Exception as exc:  # pragma: no cover
            quote_checks = []
            errors.append(f"quote_verifier_failed: {exc}")

        try:
            findings = self.fact_consistency.run(documents)
            findings = self.confidence_scorer.run(findings)
        except Exception as exc:  # pragma: no cover
            findings = []
            errors.append(f"fact_consistency_failed: {exc}")

        try:
            memo = self.judicial_memo.run(findings)
        except Exception as exc:  # pragma: no cover
            memo = "Could not generate judicial memo."
            errors.append(f"judicial_memo_failed: {exc}")

        high_conf = len([f for f in findings if f.confidence >= 0.8])
        medium_conf = len([f for f in findings if 0.5 <= f.confidence < 0.8])
        could_not_verify = len([f for f in findings if f.status == "could_not_verify"])

        summary = ReportSummary(
            total_findings=len(findings),
            high_confidence_findings=high_conf,
            medium_confidence_findings=medium_conf,
            could_not_verify=could_not_verify,
        )

        return VerificationReport(
            case_name="Rivera v. Harmon Construction Group",
            summary=summary,
            citations=citations,
            citation_verifications=citation_checks,
            quote_verifications=quote_checks,
            findings=findings,
            judicial_memo=memo,
            errors=errors,
        )
