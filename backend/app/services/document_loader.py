from __future__ import annotations

from pathlib import Path


class DocumentLoader:
    def __init__(self, documents_dir: Path):
        self.documents_dir = documents_dir

    def load_documents(self) -> dict[str, str]:
        docs: dict[str, str] = {}
        for file_path in self.documents_dir.glob("*.txt"):
            docs[file_path.stem] = file_path.read_text(encoding="utf-8")
        return docs
