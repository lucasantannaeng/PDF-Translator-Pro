"""
LLM Router Module for PDF-Translator-Pro
Manages API connections, provider routing (OpenRouter, DeepSeek, Gemini, Groq), and health checks.
"""

from __future__ import annotations
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
from core.config import config, ProviderConfig, ModelInfo


class LLMRouter:
    def __init__(self):
        self._clients: Dict[str, OpenAI] = {}

    def get_client(self, provider_name: str) -> Optional[OpenAI]:
        if provider_name in self._clients:
            return self._clients[provider_name]

        p_config = config.get_provider(provider_name)
        if not p_config or not p_config.api_key:
            return None

        client = OpenAI(
            base_url=p_config.base_url,
            api_key=p_config.api_key,
        )
        self._clients[provider_name] = client
        return client

    def get_available_models(self) -> List[Dict[str, Any]]:
        """Returns all configured models with their active provider status."""
        models = []
        for p_name, p_conf in config.list_providers().items():
            has_key = bool(p_conf.api_key)
            for m in p_conf.models:
                models.append({
                    "provider": p_name,
                    "model_id": m.id,
                    "name": m.name,
                    "cost_in": m.cost_per_1k_input,
                    "cost_out": m.cost_per_1k_output,
                    "is_ready": has_key,
                    "env_key": p_conf.env_key
                })
        return models

    def test_connection(self, provider_name: str, model_id: str) -> Tuple[bool, str, float]:
        """Tests an API provider with a small translation ping."""
        p_config = config.get_provider(provider_name)
        if not p_config:
            return False, f"Provider '{provider_name}' not found in configuration.", 0.0

        if not p_config.api_key:
            return False, f"API Key for {p_config.env_key} is missing in .env or environment.", 0.0

        client = self.get_client(provider_name)
        if not client:
            return False, "Failed to initialize API client.", 0.0

        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a translator. Translate the text to Portuguese."},
                    {"role": "user", "content": "Flight operations manual for rotorcraft."}
                ],
                max_tokens=50,
                temperature=0.1
            )
            elapsed = round(time.time() - start_time, 2)
            content = response.choices[0].message.content.strip()
            return True, f"Success! Translated: '{content}' in {elapsed}s", elapsed
        except Exception as e:
            elapsed = round(time.time() - start_time, 2)
            return False, f"API Error: {str(e)}", elapsed


router = LLMRouter()
