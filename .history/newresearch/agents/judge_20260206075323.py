"""
JudgeAgent — Agent-as-a-Judge: scores hypotheses on 4 axes.
Skipped when use_judge=false.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import JudgeOutput


class JudgeAgent(BaseAgent):
    name = "JudgeAgent"
    prompt_file = "judge.txt"
    temperature = 0.2

    def process(self, state: dict) -> dict:
        config = state["config"]
        if not config.use_judge:
            state["judge_output"] = None
            state["judge_raw"] = None
            return state

        hypothesis_output = state["hypothesis_output"]
        explorer_output = state.get("explorer_output")

        hypotheses_json = json.dumps(
            [h.model_dump() for h in hypothesis_output.hypotheses], ensure_ascii=False
        )
        evidence_json = "[]"
        if explorer_output and explorer_output.evidence_items:
            evidence_json = json.dumps(
                [e.model_dump() for e in explorer_output.evidence_items], ensure_ascii=False
            )

        persona_summary = state.get("persona_summary", "")

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            hypotheses=hypotheses_json,
            evidence=evidence_json,
            persona_summary=persona_summary,
        )

        result = self._call_llm_json(system, user_prompt)
        output = JudgeOutput(**result)
        state["judge_output"] = output
        state["judge_raw"] = result
        return state
