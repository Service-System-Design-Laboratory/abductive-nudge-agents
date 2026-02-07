"""
JudgeAgent — Diagnostic review of hypotheses (no scores).
Provides fatal_flaws, explains_confirmed, key_assumptions,
best_discriminating_question, testability & safety risk.
Skipped when use_judge=false.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import JudgeOutput


class JudgeAgent(BaseAgent):
    name = "批評家(JudgeAgent)"
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
        context_output = state["context_output"]

        hypotheses_json = json.dumps(
            [h.model_dump() for h in hypothesis_output.hypotheses], ensure_ascii=False
        )
        evidence_json = "[]"
        if explorer_output and explorer_output.evidence_items:
            evidence_json = json.dumps(
                [e.model_dump() for e in explorer_output.evidence_items], ensure_ascii=False
            )

        # Build observations list (user + external)
        all_observations = [{"id": o.id, "text": o.text} for o in context_output.observations]
        if explorer_output and explorer_output.external_observations and config.use_rag:
            for ext_obs in explorer_output.external_observations:
                all_observations.append({"id": ext_obs.id, "text": f"[外部事実] {ext_obs.text}"})
        observations_json = json.dumps(all_observations, ensure_ascii=False)

        pkg_summary = state.get("pkg_summary", "") if config.use_pkg else "(実験条件によりPKG無効)"

        config_block = self._build_config_block(config)

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            config_block=config_block,
            hypotheses=hypotheses_json,
            evidence=evidence_json,
            pkg_summary=pkg_summary,
            observations=observations_json,
        )

        result = self._call_llm_json(system, user_prompt)
        output = JudgeOutput(**result)
        state["judge_output"] = output
        state["judge_raw"] = result
        return state
