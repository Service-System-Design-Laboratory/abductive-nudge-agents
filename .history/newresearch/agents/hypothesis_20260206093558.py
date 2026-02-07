"""
HypothesisAgent — Generates 3–5 diversified abductive hypotheses.
Each hypothesis declares which O it explains, which A it assumes,
predictions, and discriminating questions.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import HypothesisOutput


class HypothesisAgent(BaseAgent):
    name = "HypothesisAgent"
    prompt_file = "hypothesis.txt"
    temperature = 0.5  # Higher for diversity

    def process(self, state: dict) -> dict:
        config = state["config"]
        context_output = state["context_output"]
        explorer_output = state.get("explorer_output")

        # Serialize inputs
        observations_json = json.dumps(
            [o.model_dump() for o in context_output.observations], ensure_ascii=False
        )
        assumptions_json = json.dumps(
            [a.model_dump() for a in context_output.assumptions], ensure_ascii=False
        )
        triggers_json = json.dumps(
            [t.model_dump() for t in context_output.triggers], ensure_ascii=False
        )
        questions_json = json.dumps(context_output.questions, ensure_ascii=False)

        evidence_json = "[]"
        if explorer_output and explorer_output.evidence_items:
            evidence_json = json.dumps(
                [e.model_dump() for e in explorer_output.evidence_items], ensure_ascii=False
            )

        persona_summary = state.get("persona_summary", "")
        pkg_summary = state.get("pkg_summary", "") if config.use_pkg else "(実験条件によりPKG無効)"

        config_block = self._build_config_block(config)

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            config_block=config_block,
            user_input=state["user_input"],
            observations=observations_json,
            assumptions=assumptions_json,
            triggers=triggers_json,
            questions=questions_json,
            evidence=evidence_json,
            persona_summary=persona_summary,
            pkg_summary=pkg_summary,
            hypothesis_count=config.hypothesis_count,
        )

        result = self._call_llm_json(system, user_prompt)

        # Post-processing: enforce empty links when config disables them
        for h in result.get("hypotheses", []):
            if not config.use_pkg:
                h["persona_link"] = []
            if not config.use_rag:
                h["evidence_link"] = []

        output = HypothesisOutput(**result)
        state["hypothesis_output"] = output
        state["hypothesis_raw"] = result
        return state
