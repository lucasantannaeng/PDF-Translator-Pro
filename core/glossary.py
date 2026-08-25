"""
Domain Glossary Manager for PDF-Translator-Pro
Provides technical terminology injection into translation prompts.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent


class GlossaryManager:
    def __init__(self, glossaries_dir: Optional[Path] = None):
        self.glossaries_dir = glossaries_dir or (BASE_DIR / "config" / "glossaries")
        self.glossaries_dir.mkdir(parents=True, exist_ok=True)
        self.active_domain: Optional[str] = "aviation"
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.load_all()

    def load_all(self) -> None:
        for json_file in self.glossaries_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._cache[json_file.stem] = data
            except Exception:
                pass

    def get_glossary(self, domain: str) -> Optional[Dict[str, Any]]:
        if domain not in self._cache:
            file_path = self.glossaries_dir / f"{domain}.json"
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    self._cache[domain] = json.load(f)
        return self._cache.get(domain)

    def format_prompt_injection(self, domain: Optional[str] = None) -> str:
        """Formats the glossary terms into a compact prompt string for LLM injection."""
        target_domain = domain or self.active_domain
        if not target_domain:
            return ""
        data = self.get_glossary(target_domain)
        if not data:
            return ""

        instructions = data.get("instructions", "")
        terms = data.get("terms", {})

        lines = [
            f"--- GLOSSÁRIO TÉCNICO E DIRETRIZES DE DOMÍNIO ({data.get('domain', target_domain)}) ---",
            instructions,
            "\nTabela de Termos Obrigatórios:",
        ]
        for src, tgt in terms.items():
            lines.append(f"- \"{src}\" => \"{tgt}\"")
        lines.append("-----------------------------------------------------------------")

        return "\n".join(lines)


glossary_manager = GlossaryManager()
