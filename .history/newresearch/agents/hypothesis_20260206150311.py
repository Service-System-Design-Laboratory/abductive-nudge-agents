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

        # Build merged observations: user observations + external observations
        all_observations = [o.model_dump() for o in context_output.observations]
        if explorer_output and explorer_output.external_observations and config.use_rag:
            for ext_obs in explorer_output.external_observations:
                all_observations.append({
                    "id": ext_obs.id,
                    "text": f"[外部事実] {ext_obs.text}",
                })

        # Serialize inputs
        observations_json = json.dumps(all_observations, ensure_ascii=False)
        assumptions_json = json.dumps(
            [a.model_dump() for a in context_output.assumptions], ensure_ascii=False
        )
        triggers_json = json.dumps(
            [t.model_dump() for t in explorer_output.triggers] if explorer_output else [],
            ensure_ascii=False,
        )
        questions_json = json.dumps(context_output.questions, ensure_ascii=False)

        evidence_json = "[]"
        if explorer_output and explorer_output.evidence_items:
            evidence_json = json.dumps(
                [e.model_dump() for e in explorer_output.evidence_items], ensure_ascii=False
            )

        # Dynamic PKG query: relevant nodes based on observations & triggers
        pkg_store = state.get("pkg_store")
        if config.use_pkg and pkg_store:
            # Extract keywords from observations and triggers
            obs_texts = [o.get("text", "") if isinstance(o, dict) else o.text for o in context_output.observations]
            trigger_texts = [t.text for t in explorer_output.triggers] if explorer_output else []
            combined = " ".join(obs_texts + trigger_texts)
            import re
            keywords = [t for t in re.findall(r'[\w]+', combined) if len(t) >= 2][:10]
            pkg_summary = pkg_store.find_relevant_nodes(keywords)
        else:
            pkg_summary = "(実験条件によりPKG無効)"

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
