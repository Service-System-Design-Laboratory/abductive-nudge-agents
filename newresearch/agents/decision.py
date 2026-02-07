"""
DecisionAgent — Selects 1 hypothesis and frames it for the user.
Selection logic differs based on whether Judge is available.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import DecisionOutput


class DecisionAgent(BaseAgent):
    name = "DecisionAgent"
    prompt_file = "decision.txt"
    temperature = 0.2

    def process(self, state: dict) -> dict:
        config = state["config"]
        hypothesis_output = state["hypothesis_output"]
        judge_output = state.get("judge_output")
        explorer_output = state.get("explorer_output")

        hypotheses_json = json.dumps(
            [h.model_dump() for h in hypothesis_output.hypotheses], ensure_ascii=False
        )

        judgements_json = "null"
        if judge_output and judge_output.judgements:
            judgements_json = json.dumps(
                [j.model_dump() for j in judge_output.judgements], ensure_ascii=False
            )

        triggers_json = json.dumps(
            [t.model_dump() for t in explorer_output.triggers] if explorer_output else [],
            ensure_ascii=False,
        )

        config_block = self._build_config_block(config)

        system = self._get_section("system")

        # Use different prompt section based on judge availability
        section = "user_with_judge" if config.use_judge else "user_without_judge"
        user_prompt = self._get_section(section).format(
            config_block=config_block,
            hypotheses=hypotheses_json,
            judgements=judgements_json,
            triggers=triggers_json,
        )

        result = self._call_llm_json(system, user_prompt)
        output = DecisionOutput(**result)
        state["decision_output"] = output
        state["decision_raw"] = result

        # Write decision to PKG (dynamic graph update)
        pkg_store = state.get("pkg_store")
        if config.use_pkg and pkg_store:
            run_id = config.run_id
            pkg_store.write_decision(
                result,
                run_id=run_id,
            )

        return state
