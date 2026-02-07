"""
ExplorerAgent — Trigger identification, RAG query generation, and evidence retrieval.
Always runs (trigger identification is unconditional).
External search is conditional on use_rag.
"""
from __future__ import annotations
import json
import logging
import os
import requests

from newresearch.agents.base import BaseAgent
from newresearch.schemas import ExplorerOutput, EvidenceItem, ExternalObservation, Trigger

logger = logging.getLogger("newresearch")


def _serper_search(query: str, num_results: int = 5) -> list[dict]:
    """Call Serper API for Google search."""
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        logger.warning("SERPER_API_KEY not set — returning empty results")
        return []
    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "gl": "jp", "hl": "ja", "num": num_results},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    results = []
    for item in data.get("organic", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "url": item.get("link", ""),
        })
    return results


class ExplorerAgent(BaseAgent):
    name = "ExplorerAgent"
    prompt_file = "explorer.txt"
    temperature = 0.2

    def process(self, state: dict) -> dict:
        config = state["config"]
        context_output = state.get("context_output")

        # ── Step 1: Trigger identification (ALWAYS runs) ───────────
        triggers, rag_queries = self._identify_triggers(state)

        # ── Step 2 & 3: Search + evidence interpretation (use_rag only)
        evidence_items = []
        ext_observations = []
        notes = ""

        if config.use_rag and rag_queries:
            evidence_items, ext_observations, notes = self._search_and_interpret(
                state, rag_queries
            )
        elif not config.use_rag:
            notes = "RAG disabled (use_rag=false) — trigger identification only"

        output = ExplorerOutput(
            triggers=triggers,
            rag_queries=rag_queries,
            evidence_items=evidence_items,
            external_observations=ext_observations,
            notes=notes,
        )
        state["explorer_output"] = output
        state["explorer_raw"] = output.model_dump()

        # Write triggers to PKG (dynamic graph update)
        pkg_store = state.get("pkg_store")
        if config.use_pkg and pkg_store and triggers:
            run_id = config.run_id
            pkg_store.write_triggers(
                [t.model_dump() for t in triggers],
                run_id=run_id,
            )

        logger.info(
            f"[ExplorerAgent] {len(triggers)} triggers, "
            f"{len(evidence_items)} evidence, "
            f"{len(ext_observations)} external observations"
        )
        return state

    def _identify_triggers(self, state: dict) -> tuple[list[Trigger], list[str]]:
        """Step 1: Identify triggers from O/A/PKG comparison (always runs)."""
        config = state["config"]
        context_output = state["context_output"]

        observations_json = json.dumps(
            [o.model_dump() for o in context_output.observations], ensure_ascii=False
        )
        assumptions_json = json.dumps(
            [a.model_dump() for a in context_output.assumptions], ensure_ascii=False
        )

        # ExplorerはO/Aの比較からトリガーを検出する（PKG読み取り不要）
        pkg_summary = "(ExplorerはPKG参照なし — O/A比較でトリガー検出)"

        config_block = self._build_config_block(config)

        system_prompt = self._get_section("system")
        user_prompt = self._get_section("user_trigger").format(
            config_block=config_block,
            user_input=state["user_input"],
            observations=observations_json,
            assumptions=assumptions_json,
            pkg_summary=pkg_summary,
        )

        try:
            data = self._call_llm_json(system=system_prompt, user=user_prompt)
        except Exception as e:
            logger.error(f"[ExplorerAgent] Trigger identification failed: {e}")
            return [Trigger(type="focus", text="trigger identification failed")], []

        triggers = []
        for t in data.get("triggers", []):
            triggers.append(Trigger(
                type=t.get("type", "focus"),
                text=t.get("text", ""),
            ))

        rag_queries = data.get("rag_queries", []) if config.use_rag else []
        return triggers, rag_queries

    def _search_and_interpret(
        self, state: dict, rag_queries: list[str]
    ) -> tuple[list[EvidenceItem], list[ExternalObservation], str]:
        """Step 2+3: Serper search + LLM interpretation (use_rag=true only)."""
        config = state["config"]

        # ── Step 2: Serper search ──────────────────────────────────
        all_results = []
        for q in rag_queries[:config.rag_top_k]:
            try:
                results = _serper_search(q, num_results=3)
                all_results.extend(results)
            except Exception as e:
                logger.error(
                    f"[ExplorerAgent] Serper search failed for query '{q}': "
                    f"{type(e).__name__}: {e}",
                    exc_info=True,
                )

        # Deduplicate by URL
        seen_urls = set()
        unique = []
        for r in all_results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                unique.append(r)
        unique = unique[:config.rag_top_k]

        if not unique:
            logger.warning("[ExplorerAgent] No search results after Serper queries")
            return [], [], "検索結果 0 件"

        # ── Step 3: LLM interpretation ─────────────────────────────
        try:
            search_results_text = json.dumps(unique, ensure_ascii=False, indent=2)
            config_block = self._build_config_block(config)

            system_prompt = self._get_section("system")
            user_prompt = self._get_section("user_evidence").format(
                config_block=config_block,
                user_input=state["user_input"],
                search_results=search_results_text,
            )

            data = self._call_llm_json(system=system_prompt, user=user_prompt)
        except Exception as e:
            logger.error(
                f"[ExplorerAgent] LLM interpretation failed: "
                f"{type(e).__name__}: {e}",
                exc_info=True,
            )
            # Fallback: use raw Serper results without LLM interpretation
            data = {
                "evidence_items": [
                    {"title": r["title"], "snippet": r["snippet"],
                     "url": r["url"], "source_type": "other"}
                    for r in unique
                ],
                "notes": f"LLM fallback — {type(e).__name__}: {e}",
            }

        # Parse evidence items
        evidence_items = []
        for i, item in enumerate(data.get("evidence_items", []), 1):
            evidence_items.append(EvidenceItem(
                rank=i,
                title=item.get("title", ""),
                snippet=item.get("snippet", ""),
                url=item.get("url", ""),
                source_type=item.get("source_type", "other"),
            ))

        # Parse external observations
        ext_observations = []
        for item in data.get("external_observations", []):
            ext_observations.append(ExternalObservation(
                id=item.get("id", f"Oext{len(ext_observations)+1}"),
                text=item.get("text", ""),
                source_url=item.get("source_url", ""),
            ))

        notes = data.get("notes", "")
        return evidence_items, ext_observations, notes
