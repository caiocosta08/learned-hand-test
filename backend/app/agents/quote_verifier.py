from __future__ import annotations

import difflib
import re
from pathlib import Path

from app.services.prompt_loader import PromptLoader
from app.schemas.report import CitationItem, QuoteVerification


DOCUMENT_KEYS_FOR_QUOTES = (
    "police_report",
    "medical_records_excerpt",
    "witness_statement",
)


def _normalize(text: str) -> str:
    text = text.lower().strip()
    return re.sub(r"\s+", " ", text)


def _best_window_match(quote: str, corpus: str) -> tuple[float, str]:
    quote_tokens = _normalize(quote).split()
    corpus_tokens = _normalize(corpus).split()
    if not quote_tokens or not corpus_tokens:
        return 0.0, ""
    size = len(quote_tokens)
    best_ratio = 0.0
    best_text = ""
    for idx in range(0, max(1, len(corpus_tokens) - size + 1)):
        window = corpus_tokens[idx : idx + size + 5]
        candidate = " ".join(window)
        ratio = difflib.SequenceMatcher(a=" ".join(quote_tokens), b=candidate).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_text = candidate
    return best_ratio, best_text


class QuoteVerifierAgent:
    def __init__(self):
        root = Path(__file__).resolve().parents[1]
        self.prompt_template = PromptLoader(root / "prompts").load("quote_verifier.md")

    def _build_verification_corpus(self, documents: dict[str, str]) -> str:
        allowed_documents: list[str] = []
        for key in DOCUMENT_KEYS_FOR_QUOTES:
            text = documents.get(key, "").strip()
            if text:
                allowed_documents.append(text)
        return "\n".join(allowed_documents)

    def run(self, citations: list[CitationItem], documents: dict[str, str]) -> list[QuoteVerification]:
        corpus = self._build_verification_corpus(documents)
        results: list[QuoteVerification] = []
        for citation in citations:
            if citation.citation_type != "quote" or not citation.quote:
                continue
            quote = citation.quote.strip()
            if not corpus:
                results.append(
                    QuoteVerification(
                        citation_id=citation.id,
                        status="could_not_verify",
                        explanation="No source documents were available for quote verification.",
                        confidence=0.2,
                    )
                )
                continue
            if quote in corpus:
                results.append(
                    QuoteVerification(
                        citation_id=citation.id,
                        status="exact_match",
                        explanation="Direct quote appears verbatim in the provided record.",
                        confidence=0.95,
                    )
                )
            else:
                ratio, match_text = _best_window_match(quote, corpus)
                if ratio >= 0.94:
                    status = "minor_difference"
                    confidence = 0.8
                    explanation = "Quote is near-verbatim with minor textual differences."
                elif ratio >= 0.78:
                    status = "material_omission"
                    confidence = 0.71
                    explanation = "Quote partially matches source but appears to omit material context."
                elif ratio >= 0.62:
                    status = "misquote"
                    confidence = 0.74
                    explanation = "Quote diverges from best matching source language."
                else:
                    status = "could_not_verify"
                    confidence = 0.3
                    explanation = "Quote text does not appear in supplied documents."
                results.append(
                    QuoteVerification(
                        citation_id=citation.id,
                        status=status,
                        explanation=explanation if not match_text else f"{explanation} Closest match: '{match_text[:140]}...'",
                        confidence=confidence,
                    )
                )
        return results
