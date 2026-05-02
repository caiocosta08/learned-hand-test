from __future__ import annotations

import json
import os
import re
from pathlib import Path

from app.services.authority_retriever import AuthorityRetriever
from app.services.prompt_loader import PromptLoader
from app.schemas.report import CitationItem, CitationVerification
from llm import call_llm


NEGATIVE_CUES = {"never", "always", "automatically", "insulating", "barred"}
QUALIFIER_CUES = {
    "generally",
    "presumptively",
    "may",
    "can",
    "depends",
    "limits",
    "context",
    "exceptions",
    "not always",
}
CONCEPT_GROUPS = {
    "liability": {"liable", "liability", "negligence", "tort"},
    "control": {"control", "controlled", "retained", "delegated"},
    "safety": {"osha", "safety", "compliance", "standard", "care"},
    "contractor": {"hirer", "contractor", "subcontractor", "employee"},
}


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9']+", text.lower())
        if len(token) > 3
    }


def _keyword_score(claim: str, text: str) -> float:
    claim_tokens = _tokenize(claim)
    text_tokens = _tokenize(text)
    if not claim_tokens:
        return 0.0
    overlap = len(claim_tokens & text_tokens)
    return overlap / len(claim_tokens)


def _concept_score(claim: str, text: str) -> float:
    claim_tokens = _tokenize(claim)
    text_tokens = _tokenize(text)
    mapped_claim = {
        label for label, variants in CONCEPT_GROUPS.items() if claim_tokens & variants
    }
    mapped_text = {
        label for label, variants in CONCEPT_GROUPS.items() if text_tokens & variants
    }
    if not mapped_claim:
        return 0.0
    return len(mapped_claim & mapped_text) / len(mapped_claim)


def _has_any_phrase(text: str, phrases: set[str]) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in phrases)


def _semantic_assessment(claim: str, authority: dict[str, str]) -> tuple[str, bool | None, float, str]:
    holding = authority.get("holding", "")
    excerpt = authority.get("excerpt", "")
    evidence_text = f"{holding} {excerpt}".strip()
    lexical = _keyword_score(claim, evidence_text)
    concept = _concept_score(claim, evidence_text)
    negative_claim = _has_any_phrase(claim, NEGATIVE_CUES)
    qualified_authority = _has_any_phrase(evidence_text, QUALIFIER_CUES)
    contradiction_penalty = 0.2 if negative_claim and qualified_authority else 0.0
    semantic = max(0.0, 0.55 * lexical + 0.45 * concept - contradiction_penalty)

    if semantic >= 0.72:
        return ("full", True, 0.82, "Strong semantic alignment between claim and authority text.")
    if semantic >= 0.45:
        return (
            "partial",
            True,
            0.68,
            "Authority supports part of the proposition, with qualifiers or narrower scope.",
        )
    if semantic >= 0.25:
        return (
            "partial",
            None,
            0.55,
            "Authority relevance detected, but support is ambiguous from available excerpts.",
        )
    return ("none", False, 0.6, "Authority text does not substantively support the stated proposition.")


class AuthorityVerifierAgent:
    def __init__(self):
        root = Path(__file__).resolve().parents[1]
        self.prompt_loader = PromptLoader(root / "prompts")
        self.retriever = AuthorityRetriever(root.parent / "documents" / "authority_library.json")

    def _llm_assess(self, citation: CitationItem, authority: dict[str, str]) -> dict | None:
        if os.getenv("BS_DETECTOR_DISABLE_LLM", "0") == "1":
            return None
        if not os.getenv("OPENAI_API_KEY"):
            return None
        prompt = self.prompt_loader.load("authority_verifier.md")
        payload = {
            "claim": citation.claim,
            "citation": citation.citation,
            "authority": authority,
        }
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps(payload)},
        ]
        response = call_llm(messages=messages, model="gpt-4o-mini", temperature=0)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return None

    def run(self, citations: list[CitationItem], documents: dict[str, str]) -> list[CitationVerification]:
        results: list[CitationVerification] = []
        for citation in citations:
            if citation.citation_type == "case_law":
                authority = self.retriever.get_authority(citation.citation)
                if not authority:
                    results.append(
                        CitationVerification(
                            citation_id=citation.id,
                            supports_claim=None,
                            support_level="could_not_verify",
                            explanation="Authority text unavailable in local/known sources.",
                            confidence=0.2,
                        )
                    )
                    continue

                llm_result = self._llm_assess(citation, authority)
                score = _keyword_score(citation.claim, authority.get("holding", ""))
                should_use_llm = 0.2 <= score <= 0.65
                if llm_result and should_use_llm:
                    results.append(
                        CitationVerification(
                            citation_id=citation.id,
                            supports_claim=llm_result.get("supports_claim"),
                            support_level=llm_result.get("support_level", "could_not_verify"),
                            explanation=llm_result.get("explanation", "No explanation."),
                            confidence=float(llm_result.get("confidence", 0.5)),
                        )
                    )
                    continue
                support_level, supports_claim, confidence, explanation = _semantic_assessment(
                    citation.claim,
                    authority,
                )
                results.append(
                    CitationVerification(
                        citation_id=citation.id,
                        supports_claim=supports_claim,
                        support_level=support_level,
                        explanation=explanation,
                        confidence=confidence,
                    )
                )
                continue

            if citation.citation_type == "quote":
                results.append(
                    CitationVerification(
                        citation_id=citation.id,
                        supports_claim=None,
                        support_level="could_not_verify",
                        explanation="Quoted source is not explicitly traceable to a document section.",
                        confidence=0.35,
                    )
                )
                continue

            results.append(
                CitationVerification(
                    citation_id=citation.id,
                    supports_claim=None,
                    support_level="could_not_verify",
                    explanation="Unsupported citation type.",
                    confidence=0.2,
                )
            )
        return results
