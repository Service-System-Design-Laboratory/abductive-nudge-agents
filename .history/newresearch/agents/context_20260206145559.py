"""
ContextAgent — Extracts Observations (O), Assumptions (A), and questions.
Establishes dialogue grounding by aligning user input with PKG.
Trigger identification and RAG queries are handled by ExplorerAgent.
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
        pkg_summary = state.get("pkg_summary", "")
        config = state["config"]
        use_pkg = config.use_pkg

        config_block = self._build_config_block(config)

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            config_block=config_block,
            user_input=user_input,
            pkg_summary=pkg_summary if use_pkg else "(実験条件によりPKG無効)",
        )

        result = self._call_llm_json(system, user_prompt)
        output = ContextOutput(**result)
        state["context_output"] = output
        state["context_raw"] = result
        return state
