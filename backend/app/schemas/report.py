from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SupportLevel = Literal["full", "partial", "none", "could_not_verify"]
QuoteStatus = Literal[
    "exact_match",
    "minor_difference",
    "material_omission",
    "misquote",
    "could_not_verify",
]


class CitationItem(BaseModel):
    id: str
    claim: str
    citation: str
    quote: str | None = None
    page: int | None = None
    citation_type: Literal["case_law", "document", "quote", "unknown"]


class CitationVerification(BaseModel):
    citation_id: str
    supports_claim: bool | None = None
    support_level: SupportLevel
    explanation: str
    confidence: float = Field(ge=0, le=1)


class QuoteVerification(BaseModel):
    citation_id: str
    status: QuoteStatus
    explanation: str
    confidence: float = Field(ge=0, le=1)


class FindingEvidence(BaseModel):
    motion_excerpt: str
    source_excerpt: str
    source_document: str


class Finding(BaseModel):
    id: str
    type: str
    severity: Literal["low", "medium", "high"]
    confidence: float = Field(ge=0, le=1)
    motion_claim: str
    citation: str | None = None
    assessment: str
    reasoning: str
    status: Literal["verified_issue", "could_not_verify", "no_issue"]
    evidence: FindingEvidence | None = None


class ReportSummary(BaseModel):
    total_findings: int
    high_confidence_findings: int
    medium_confidence_findings: int
    could_not_verify: int


class VerificationReport(BaseModel):
    case_name: str
    summary: ReportSummary
    citations: list[CitationItem]
    citation_verifications: list[CitationVerification]
    quote_verifications: list[QuoteVerification]
    findings: list[Finding]
    judicial_memo: str
    errors: list[str]
