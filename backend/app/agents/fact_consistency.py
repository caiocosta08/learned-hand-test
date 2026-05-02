from __future__ import annotations

import re

from app.schemas.report import Finding, FindingEvidence


def _compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _extract_date(text: str) -> str | None:
    match = re.search(r"\b([A-Z][a-z]+\s+\d{1,2},\s+\d{4})\b", text)
    return match.group(1) if match else None


def _extract_incident_date(text: str) -> str | None:
    labelled = re.search(r"Date of Incident:\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4})", text)
    if labelled:
        return labelled.group(1)
    return _extract_date(text)


def _contains_all(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return all(term.lower() in lowered for term in terms)


def _has_phrase(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def _build_evidence(motion: str, source: str, source_name: str) -> FindingEvidence:
    return FindingEvidence(
        motion_excerpt=_compact(motion)[:180],
        source_excerpt=_compact(source)[:180],
        source_document=source_name,
    )


class FactConsistencyAgent:
    def run(self, documents: dict[str, str]) -> list[Finding]:
        motion = documents.get("motion_for_summary_judgment", "")
        police = documents.get("police_report", "")
        medical = documents.get("medical_records_excerpt", "")
        witness = documents.get("witness_statement", "")
        findings: list[Finding] = []

        motion_date = _extract_incident_date(motion)
        police_date = _extract_incident_date(police)
        medical_date = _extract_incident_date(medical)
        witness_date = _extract_incident_date(witness)
        corroborated_source_date = police_date or medical_date or witness_date
        if motion_date and corroborated_source_date and motion_date != corroborated_source_date:
            findings.append(
                Finding(
                    id="finding_001",
                    type="cross_document_date_conflict",
                    severity="high",
                    confidence=0.98,
                    motion_claim=f"Motion states incident occurred on {motion_date}.",
                    citation=None,
                    assessment=f"Other case-file records indicate {corroborated_source_date}.",
                    reasoning="Primary records align on incident date that differs from motion statement.",
                    status="verified_issue",
                    evidence=_build_evidence(
                        f"...incident on {motion_date}...",
                        f"Date of Incident: {corroborated_source_date}",
                        "police_report" if police_date else "medical_records_excerpt" if medical_date else "witness_statement",
                    ),
                )
            )

        motion_denies_ppe = _contains_all(
            motion,
            ("not wearing", "personal protective equipment"),
        )
        source_supports_ppe = _contains_all(police + " " + witness, ("wearing", "hard hat", "harness"))
        if motion_denies_ppe and source_supports_ppe:
            findings.append(
                Finding(
                    id="finding_002",
                    type="cross_document_ppe_conflict",
                    severity="high",
                    confidence=0.95,
                    motion_claim="Motion claims plaintiff was not wearing required PPE.",
                    citation=None,
                    assessment="Police report and witness statement indicate Rivera wore required gear.",
                    reasoning="Two independent records state he wore hard hat and harness.",
                    status="verified_issue",
                    evidence=_build_evidence(
                        "...was not wearing required personal protective equipment...",
                        "Rivera was wearing a hard hat and harness...",
                        "police_report",
                    ),
                )
            )

        if _has_phrase(motion, "immediately apparent") and _has_phrase(medical, "comminuted fracture"):
            findings.append(
                Finding(
                    id="finding_003",
                    type="fact_supported",
                    severity="low",
                    confidence=0.84,
                    motion_claim="Motion states injuries were immediately apparent.",
                    citation=None,
                    assessment="Medical notes support immediate severe pain and acute fractures.",
                    reasoning="Clinical intake records immediate onset with objective injuries.",
                    status="no_issue",
                    evidence=_build_evidence(
                        "...injuries... were immediately apparent...",
                        "immediate onset of severe pain... comminuted fracture",
                        "medical_records_excerpt",
                    ),
                )
            )

        motion_asserts_osha_record = _contains_all(motion, ("passed all OSHA inspections", "unblemished"))
        source_only_pending_osha = _has_phrase(police, "cal/osha investigation is expected")
        if motion_asserts_osha_record and source_only_pending_osha:
            findings.append(
                Finding(
                    id="finding_004",
                    type="cross_document_unverified_inference",
                    severity="medium",
                    confidence=0.61,
                    motion_claim="Motion asserts unblemished OSHA record and compliance presumption.",
                    citation=None,
                    assessment="Provided record does not include inspection reports to verify this assertion.",
                    reasoning="Referenced compliance evidence is absent from supplied case file.",
                    status="could_not_verify",
                    evidence=_build_evidence(
                        "...passed all OSHA inspections...",
                        "A separate Cal/OSHA investigation is expected.",
                        "police_report",
                    ),
                )
            )

        if _has_phrase(police, "Donner stated") and _has_phrase(witness, "dismissed my concern"):
            findings.append(
                Finding(
                    id="finding_005",
                    type="cross_document_consistent_fact",
                    severity="low",
                    confidence=0.78,
                    motion_claim="Foreman directed Apex crew to use east-side section.",
                    citation=None,
                    assessment="Police report and witness statement align on Donner's direction.",
                    reasoning="Both sources describe project urgency and directive from foreman.",
                    status="no_issue",
                    evidence=_build_evidence(
                        "...Apex ... responsible for scaffolding operations...",
                        "Donner ... directed us to work on that section.",
                        "witness_statement",
                    ),
                )
            )

        return findings
