"""
DialogueAgent — Generates the final empathetic response with nudge markers.
Embeds discriminating questions to close the abductive loop.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import DialogueOutput


class DialogueAgent(BaseAgent):
    name = "DialogueAgent"
    prompt_file = "dialogue.txt"
    temperature = 0.3

    def process(self, state: dict) -> dict:
        hypothesis_output = state["hypothesis_output"]
        decision_output = state["decision_output"]

        # Find the selected hypothesis
        selected_id = decision_output.selected_hypothesis_id
        selected_h = None
        for h in hypothesis_output.hypotheses:
            if h.hypothesis_id == selected_id:
                selected_h = h
                break
        if selected_h is None:
            selected_h = hypothesis_output.hypotheses[0]

        selected_json = json.dumps(selected_h.model_dump(), ensure_ascii=False)
        frame_json = json.dumps(decision_output.user_facing_frame.model_dump(), ensure_ascii=False)

        persona_summary = state.get("persona_summary", "")

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            user_input=state["user_input"],
            selected_hypothesis=selected_json,
            user_facing_frame=frame_json,
            persona_summary=persona_summary,
        )

        result = self._call_llm_json(system, user_prompt)
        output = DialogueOutput(**result)
        state["dialogue_output"] = output
        state["dialogue_raw"] = result
        return state
