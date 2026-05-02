from __future__ import annotations

import json
from pathlib import Path


class AuthorityRetriever:
    def __init__(self, library_path: Path):
        self.library_path = library_path

    def _load(self) -> dict[str, dict[str, str]]:
        if not self.library_path.exists():
            return {}
        return json.loads(self.library_path.read_text(encoding="utf-8"))

    def get_authority(self, citation: str) -> dict[str, str] | None:
        library = self._load()
        key = citation.strip().lower()
        exact = library.get(key)
        if exact:
            return exact
        for lib_key, value in library.items():
            case_name = lib_key.split(",", 1)[0]
            if case_name and case_name in key:
                return value
        return None
