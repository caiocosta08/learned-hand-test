from __future__ import annotations

from app.schemas.report import Finding


class JudicialMemoAgent:
    def run(self, findings: list[Finding]) -> str:
        issues = [f for f in findings if f.status == "verified_issue"]
        if not issues:
            return (
                "The submitted motion does not show clear record-level contradictions in the "
                "provided file, but several legal authorities remain unverified because source "
                "opinions were not included."
            )
        top = sorted(issues, key=lambda item: item.confidence, reverse=True)[:2]
        highlights = "; ".join(f.assessment for f in top)
        return (
            "The record review identifies material reliability concerns in the motion. "
            f"Most notably, {highlights}. "
            "These discrepancies should be weighed before relying on the motion's factual framing."
        )
