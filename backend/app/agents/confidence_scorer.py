from __future__ import annotations

from app.schemas.report import Finding


class ConfidenceScorerAgent:
    def run(self, findings: list[Finding]) -> list[Finding]:
        scored: list[Finding] = []
        for finding in findings:
            multiplier = 1.0
            if finding.status == "could_not_verify":
                multiplier = 0.9
            if finding.severity == "high" and finding.status == "verified_issue":
                multiplier = 1.0
            new_confidence = min(1.0, round(finding.confidence * multiplier, 2))
            scored.append(finding.model_copy(update={"confidence": new_confidence}))
        return scored
