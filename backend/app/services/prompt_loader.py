from __future__ import annotations

from pathlib import Path


class PromptLoader:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = prompts_dir

    def load(self, file_name: str) -> str:
        path = self.prompts_dir / file_name
        return path.read_text(encoding="utf-8")
