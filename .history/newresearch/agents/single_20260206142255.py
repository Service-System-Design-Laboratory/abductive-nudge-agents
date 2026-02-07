"""
SingleAgent — monolithic baseline that produces a response in ONE LLM call.
No pipeline decomposition: no Context/Explorer/Hypothesis/Judge/Decision stages.
Used as Condition D to compare against the multi-agent abductive pipeline.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import DialogueOutput


class SingleAgent(BaseAgent):
    name = "SingleAgent"
    prompt_file = "single.txt"
    temperature = 0.3

    def process(self, state: dict) -> dict:
        persona_summary = state.get("persona_summary", "")

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            user_input=state["user_input"],
            persona_summary=persona_summary or "(ペルソナ情報なし)",
        )

        raw = self._call_llm_json(system, user_prompt)

        output = DialogueOutput(**raw)
        state["dialogue_output"] = output
        state["dialogue_raw"] = raw
        return state
