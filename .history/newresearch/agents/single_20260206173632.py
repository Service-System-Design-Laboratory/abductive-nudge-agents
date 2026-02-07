"""
SingleAgent — CoT baseline that produces ALL structured outputs in ONE LLM call.
Same reasoning steps as the multi-agent pipeline (Context→Explorer→Hypothesis→
Judge→Decision→Dialogue), but executed as a single Chain-of-Thought.
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
        import json as _json

        # Dynamic PKG query: combine top nodes + interests for full context
        pkg_store = state.get("pkg_store")
        if pkg_store and pkg_store.enabled:
            top_nodes = pkg_store.get_top_nodes(8)
            interests = pkg_store.get_interests_and_values()
            pkg_summary = f"{top_nodes}\n\n{interests}"
        else:
            pkg_summary = "(PKG情報なし)"

        rag_results = state.get("rag_results", [])

        # Format RAG results for prompt injection
        if rag_results:
            rag_text = _json.dumps(rag_results, ensure_ascii=False, indent=2)
        else:
            rag_text = "(外部検索結果なし)"

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            user_input=state["user_input"],
            pkg_summary=pkg_summary,
            rag_results=rag_text,
        )

        raw = self._call_llm_json(system, user_prompt)

        # Extract structured intermediate artifacts from CoT output
        # context.json equivalent
        if "context" in raw:
            state["context_raw"] = raw["context"]

        # evidence.json equivalent (triggers + external_observations)
        if "evidence" in raw:
            state["evidence_raw"] = raw["evidence"]

        # hypotheses.json equivalent
        if "hypotheses" in raw:
            state["hypotheses_raw"] = {"hypotheses": raw["hypotheses"]}

        # judgements.json equivalent
        if "judgements" in raw:
            state["judgements_raw"] = {"judgements": raw["judgements"]}

        # decision.json equivalent
        if "decision" in raw:
            state["decision_raw"] = raw["decision"]

        # DialogueOutput (final_response + markers)
        dialogue_data = {
            "final_response": raw.get("final_response", ""),
            "markers": raw.get("markers", {}),
        }
        output = DialogueOutput(**dialogue_data)
        state["dialogue_output"] = output
        state["dialogue_raw"] = raw
        return state
