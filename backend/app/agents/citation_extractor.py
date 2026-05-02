from __future__ import annotations

import re
from pathlib import Path

from app.services.prompt_loader import PromptLoader
from app.schemas.report import CitationItem


CASE_CITATION_PATTERN = re.compile(
    r"([A-Z][A-Za-z' .,&-]+ v\. [A-Z][A-Za-z' .,&-]+,\s*[^\n;]+?\(\d{4}\))"
)
STATUTE_CITATION_PATTERN = re.compile(
    r"(California Code of Civil Procedure Section\s+\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
SENTENCE_END_PATTERN = re.compile(r"[.!?]")


def _sentence_for_index(text: str, index: int) -> str:
    left = 0
    right = len(text)
    for match in SENTENCE_END_PATTERN.finditer(text):
        if match.start() < index:
            left = match.end()
        elif match.start() >= index:
            right = match.end()
            break
    return " ".join(text[left:right].strip().split())


class CitationExtractorAgent:
    def __init__(self):
        root = Path(__file__).resolve().parents[1]
        self.prompt_template = PromptLoader(root / "prompts").load("citation_extractor.md")

    def run(self, motion_text: str) -> list[CitationItem]:
        if not motion_text.strip():
            return []
        items: list[CitationItem] = []
        seen: set[str] = set()
        for idx, match in enumerate(CASE_CITATION_PATTERN.finditer(motion_text), start=1):
            citation_text = match.group(1).strip()
            if citation_text.lower() in seen:
                continue
            seen.add(citation_text.lower())
            claim = _sentence_for_index(motion_text, match.start())
            items.append(
                CitationItem(
                    id=f"citation_{idx:03d}",
                    claim=claim,
                    citation=citation_text,
                    quote=None,
                    page=None,
                    citation_type="case_law",
                )
            )

        quote_matches = re.finditer(r'"([^"]{8,})"', motion_text)
        seen_quotes: set[str] = set()
        base = len(items)
        for qidx, match in enumerate(quote_matches, start=1):
            quote_text = match.group(1).strip()
            quote_key = quote_text.lower()
            if quote_key in seen_quotes:
                continue
            seen_quotes.add(quote_key)
            claim = _sentence_for_index(motion_text, match.start())
            citation_context = _sentence_for_index(motion_text, match.end())
            items.append(
                CitationItem(
                    id=f"citation_{base + qidx:03d}",
                    claim=claim,
                    citation=citation_context,
                    quote=quote_text,
                    page=None,
                    citation_type="quote",
                )
            )

        base = len(items)
        for sidx, match in enumerate(STATUTE_CITATION_PATTERN.finditer(motion_text), start=1):
            citation_text = match.group(1).strip()
            if citation_text.lower() in seen:
                continue
            seen.add(citation_text.lower())
            claim = _sentence_for_index(motion_text, match.start())
            items.append(
                CitationItem(
                    id=f"citation_{base + sidx:03d}",
                    claim=claim,
                    citation=citation_text,
                    quote=None,
                    page=None,
                    citation_type="document",
                )
            )
        return items
