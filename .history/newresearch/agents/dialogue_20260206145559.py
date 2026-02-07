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
        config = state["config"]
        hypothesis_output = state["hypothesis_output"]
        decision_output = state["decision_output"]

        # Find the selected hypothesis
        selected_id = decision_output.selected_hypothesis_id
        contrasting_id = decision_output.contrasting_hypothesis_id
        selected_h = None
        contrasting_h = None
        for h in hypothesis_output.hypotheses:
            if h.hypothesis_id == selected_id:
                selected_h = h
            if h.hypothesis_id == contrasting_id:
                contrasting_h = h
        if selected_h is None:
            selected_h = hypothesis_output.hypotheses[0]

        selected_json = json.dumps(selected_h.model_dump(), ensure_ascii=False)
        contrasting_json = json.dumps(contrasting_h.model_dump(), ensure_ascii=False) if contrasting_h else "null"
        frame_json = json.dumps(decision_output.user_facing_frame.model_dump(), ensure_ascii=False)

        pkg_summary = state.get("pkg_summary", "") if config.use_pkg else "(実験条件によりPKG無効)"
        config_block = self._build_config_block(config)

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            config_block=config_block,
            user_input=state["user_input"],
            selected_hypothesis=selected_json,
            contrasting_hypothesis=contrasting_json,
            user_facing_frame=frame_json,
            pkg_summary=pkg_summary,
        )

        result = self._call_llm_json(system, user_prompt)
        output = DialogueOutput(**result)
        state["dialogue_output"] = output
        state["dialogue_raw"] = result
        return state
