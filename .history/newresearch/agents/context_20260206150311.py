"""
ContextAgent — Extracts Observations (O), Assumptions (A), and questions.
Establishes dialogue grounding by aligning user input with PKG.
Trigger identification and RAG queries are handled by ExplorerAgent.
"""
from __future__ import annotations
import json

from newresearch.agents.base import BaseAgent
from newresearch.schemas import ContextOutput


class ContextAgent(BaseAgent):
    name = "ContextAgent"
    prompt_file = "context.txt"
    temperature = 0.2

    def process(self, state: dict) -> dict:
        user_input = state["user_input"]
        config = state["config"]
        use_pkg = config.use_pkg

        # Dynamic PKG query: keyword-based subgraph retrieval
        pkg_store = state.get("pkg_store")
        if use_pkg and pkg_store:
            keywords = self._extract_keywords(user_input)
            pkg_summary = pkg_store.find_relevant_nodes(keywords)
        else:
            pkg_summary = "(実験条件によりPKG無効)"

        config_block = self._build_config_block(config)

        system = self._get_section("system")
        user_prompt = self._get_section("user").format(
            config_block=config_block,
            user_input=user_input,
            pkg_summary=pkg_summary,
        )

        result = self._call_llm_json(system, user_prompt)
        output = ContextOutput(**result)
        state["context_output"] = output
        state["context_raw"] = result
        return state

    @staticmethod
    def _extract_keywords(text: str) -> list[str]:
        """Simple keyword extraction from user input for PKG query."""
        import re
        # Remove common particles and short tokens
        stop = {'の', 'は', 'が', 'を', 'に', 'で', 'と', 'も', 'か', 'な', 'て', 'し',
                'た', 'だ', 'です', 'ます', 'する', 'ない', 'ある', 'いる', 'れる',
                'って', 'から', 'まで', 'より', 'ため', 'こと', 'もの', 'けど', 'けれど',
                'でも', 'しか', 'ので', 'のに', 'ばかり', 'だけ'}
        # Split on non-word chars and keep tokens ≥2 chars
        tokens = re.findall(r'[\w]+', text)
        keywords = [t for t in tokens if len(t) >= 2 and t not in stop]
        return keywords[:10]  # limit to 10 keywords
