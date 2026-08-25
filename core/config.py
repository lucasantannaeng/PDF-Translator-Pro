"""
Configuration Manager for PDF-Translator-Pro
Loads settings from YAML and environment variables.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import yaml
from dotenv import load_dotenv

# Project Root Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file with override
load_dotenv(BASE_DIR / ".env", override=True)


@dataclass
class ModelInfo:
    id: str
    name: str
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0


@dataclass
class ProviderConfig:
    name: str
    base_url: str
    env_key: str
    api_key: Optional[str] = None
    models: List[ModelInfo] = field(default_factory=list)


class Settings:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (BASE_DIR / "config" / "settings.yaml")
        self.raw: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.raw = yaml.safe_load(f) or {}
        else:
            self.raw = {}

    @property
    def source_lang(self) -> str:
        return self.raw.get("translation", {}).get("source_lang", "en")

    @property
    def target_lang(self) -> str:
        return self.raw.get("translation", {}).get("target_lang", "pt")

    @property
    def default_provider(self) -> str:
        return os.getenv("DEFAULT_PROVIDER") or self.raw.get("translation", {}).get("default_provider", "openrouter")

    @property
    def default_model(self) -> str:
        return os.getenv("DEFAULT_MODEL") or self.raw.get("translation", {}).get("default_model", "deepseek/deepseek-chat")

    @property
    def concurrency(self) -> int:
        return int(self.raw.get("translation", {}).get("concurrency", 4))

    @property
    def output_format(self) -> str:
        return self.raw.get("translation", {}).get("output_format", "both")

    @property
    def preserve_math(self) -> bool:
        return bool(self.raw.get("translation", {}).get("preserve_math", True))

    @property
    def input_dir(self) -> Path:
        p = BASE_DIR / self.raw.get("paths", {}).get("input_dir", "input_pdfs")
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def output_dir(self) -> Path:
        p = BASE_DIR / self.raw.get("paths", {}).get("output_dir", "output_translated")
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def logs_dir(self) -> Path:
        p = BASE_DIR / self.raw.get("paths", {}).get("logs_dir", "logs")
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def temp_dir(self) -> Path:
        p = BASE_DIR / self.raw.get("paths", {}).get("temp_dir", "temp")
        p.mkdir(parents=True, exist_ok=True)
        return p

    def get_provider(self, name: str) -> Optional[ProviderConfig]:
        providers_data = self.raw.get("providers", {})
        if name not in providers_data:
            return None
        p_data = providers_data[name]
        env_key = p_data.get("env_key", "")
        api_key = os.getenv(env_key) or p_data.get("api_key")

        models = [
            ModelInfo(
                id=m["id"],
                name=m["name"],
                cost_per_1k_input=m.get("cost_per_1k_input", 0.0),
                cost_per_1k_output=m.get("cost_per_1k_output", 0.0),
            )
            for m in p_data.get("models", [])
        ]

        return ProviderConfig(
            name=name,
            base_url=p_data.get("base_url", ""),
            env_key=env_key,
            api_key=api_key,
            models=models,
        )

    def list_providers(self) -> Dict[str, ProviderConfig]:
        res = {}
        for name in self.raw.get("providers", {}):
            p = self.get_provider(name)
            if p:
                res[name] = p
        return res


config = Settings()
