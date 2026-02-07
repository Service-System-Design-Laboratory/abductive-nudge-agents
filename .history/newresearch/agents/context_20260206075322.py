"""
ContextAgent — Extracts Observations (O), Assumptions (A), triggers, and RAG queries.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import ContextOutput


class ContextAgent(BaseAgent):
    name = "ContextAgent"
    prompt_file = "context.txt"
    temperature = 0.2

    def process(self, state: dict) -> dict:
        user_input = state["user_input"]
        persona_summary = state.get("persona_summary", "")
        pkg_summary = state.get("pkg_summary", "")
        use_pkg = state["config"].use_pkg

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            user_input=user_input,
            persona_summary=persona_summary,
            pkg_summary=pkg_summary if use_pkg else "(PKG無効)",
        )

        result = self._call_llm_json(system, user_prompt)
        output = ContextOutput(**result)
        state["context_output"] = output
        state["context_raw"] = result
        return state
