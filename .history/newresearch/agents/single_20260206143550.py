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
        import json as _json

        persona_summary = state.get("persona_summary", "")
        pkg_summary = state.get("pkg_summary", "")
        rag_results = state.get("rag_results", [])

        # Format RAG results for prompt injection
        if rag_results:
            rag_text = _json.dumps(rag_results, ensure_ascii=False, indent=2)
        else:
            rag_text = "(外部検索結果なし)"

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            user_input=state["user_input"],
            persona_summary=persona_summary or "(ペルソナ情報なし)",
            pkg_summary=pkg_summary or "(PKG情報なし)",
            rag_results=rag_text,
        )

        raw = self._call_llm_json(system, user_prompt)

        output = DialogueOutput(**raw)
        state["dialogue_output"] = output
        state["dialogue_raw"] = raw
        return state
