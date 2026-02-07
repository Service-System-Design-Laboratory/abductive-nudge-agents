"""
BaseAgent — shared LLM call, prompt loading, and logging infrastructure.
All 6 pipeline agents inherit from this.
"""
from __future__ import annotations
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import openai

from newresearch.config import azure_settings

logger = logging.getLogger("newresearch")

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


class BaseAgent:
    """Base class for all pipeline agents."""

    name: str = "BaseAgent"
    prompt_file: str = ""
    temperature: float = 0.2

    def __init__(self):
        self._client = openai.AzureOpenAI(
            api_key=azure_settings.api_key,
            api_version=azure_settings.api_version,
            azure_endpoint=azure_settings.endpoint,
        )
        self._model = azure_settings.deployment
        self._prompt_sections: Dict[str, str] = {}
        if self.prompt_file:
            self._load_prompt()

    # ── Prompt loading ─────────────────────────────────────────────

    def _load_prompt(self):
        """Load prompt file and split into sections by '### Section: <name>'."""
        path = PROMPTS_DIR / self.prompt_file
        if not path.exists():
            logger.warning(f"Prompt file not found: {path}")
            return
        text = path.read_text(encoding="utf-8")
        current_section = "default"
        lines: Dict[str, list] = {current_section: []}
        for line in text.splitlines():
            if line.startswith("### Section:"):
                current_section = line.split(":", 1)[1].strip()
                lines[current_section] = []
            else:
                lines[current_section].append(line)
        self._prompt_sections = {k: "\n".join(v).strip() for k, v in lines.items()}

    def _get_section(self, name: str) -> str:
        return self._prompt_sections.get(name, "")

    # ── LLM call ───────────────────────────────────────────────────

    def _call_llm(
        self,
        system: str,
        user: str,
        temperature: Optional[float] = None,
        use_json: bool = True,
    ) -> str:
        """Call Azure OpenAI and return the raw response string."""
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        kwargs: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature or self.temperature,
        }
        if use_json:
            kwargs["response_format"] = {"type": "json_object"}

        logger.info(f"[{self.name}] LLM call ({len(system)+len(user)} chars)")
        response = self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content or ""
        logger.info(f"[{self.name}] Response ({len(content)} chars)")
        return content

    def _call_llm_json(self, system: str, user: str, **kwargs) -> dict:
        """Call LLM and parse response as JSON. Retry once on parse failure."""
        raw = self._call_llm(system, user, use_json=True, **kwargs)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning(f"[{self.name}] JSON parse failed, retrying with repair prompt")
            repair = self._call_llm(
                system="次のテキストを有効なJSON形式に修正してください。内容は変えないでください。",
                user=raw,
                use_json=True,
            )
            return json.loads(repair)

    # ── Config block helper ─────────────────────────────────────────

    @staticmethod
    def _build_config_block(config) -> str:
        """Build a human-readable config flags block for prompt injection."""
        return (
            f"use_pkg = {str(config.use_pkg).lower()}   ← PKGの利用{'可' if config.use_pkg else '不可'}\n"
            f"use_rag = {str(config.use_rag).lower()}   ← 外部エビデンス(RAG)の利用{'可' if config.use_rag else '不可'}\n"
            f"use_judge = {str(config.use_judge).lower()} ← Judge評価の利用{'可' if config.use_judge else '不可'}"
        )

    # ── Abstract process ───────────────────────────────────────────

    def process(self, state: dict) -> dict:
        """Override in subclass. Takes full pipeline state, returns updated state."""
        raise NotImplementedError
