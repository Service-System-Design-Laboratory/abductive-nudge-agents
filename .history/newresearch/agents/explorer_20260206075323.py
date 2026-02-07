"""
ExplorerAgent — External evidence retrieval via Serper API (RAG).
Skipped when use_rag=false.
"""
from __future__ import annotations
import json
import logging
import os
import requests

from newresearch.agents.base import BaseAgent
from newresearch.schemas import ExplorerOutput, EvidenceItem

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
        if not config.use_rag:
            state["explorer_output"] = ExplorerOutput(
                evidence_items=[], notes="RAG disabled (use_rag=false)"
            )
            state["explorer_raw"] = state["explorer_output"].model_dump()
            return state

        # Get RAG queries from ContextAgent
        context_output = state.get("context_output")
        rag_queries = context_output.rag_queries if context_output else []
        if not rag_queries:
            rag_queries = state.get("context_raw", {}).get("rag_queries", [])

        # Search
        all_results = []
        for q in rag_queries[:config.rag_top_k]:
            results = _serper_search(q, num_results=3)
            all_results.extend(results)

        # Deduplicate by URL
        seen_urls = set()
        unique = []
        for r in all_results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                unique.append(r)

        # Build evidence items
        evidence_items = []
        for i, r in enumerate(unique[:config.rag_top_k], 1):
            # Classify source type
            url = r.get("url", "")
            source_type = "other"
            if ".edu" in url or ".ac.jp" in url:
                source_type = "edu"
            elif ".gov" in url or ".go.jp" in url:
                source_type = "gov"
            elif ".org" in url:
                source_type = "org"
            elif ".com" in url:
                source_type = "com"

            evidence_items.append(EvidenceItem(
                rank=i,
                title=r["title"],
                snippet=r["snippet"],
                url=url,
                source_type=source_type,
            ))

        output = ExplorerOutput(evidence_items=evidence_items)
        state["explorer_output"] = output
        state["explorer_raw"] = output.model_dump()
        logger.info(f"[ExplorerAgent] Found {len(evidence_items)} evidence items")
        return state
