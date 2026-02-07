"""
SinglePipeline — minimal pipeline for Condition D (Single Agent baseline).
Runs only the SingleAgent (1 LLM call) with the SAME information sources
(PKG + RAG) as the multi-agent pipeline. The only difference is
no pipeline decomposition.
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import requests

from newresearch.config import RunConfig
from newresearch.schemas import Persona
from newresearch.pkg_store import PKGStore
from newresearch.agents.single import SingleAgent

logger = logging.getLogger("newresearch")

RUNS_DIR = Path(__file__).parent / "results" / "runs"


def _serper_search(query: str, num_results: int = 3) -> list[dict]:
    """Call Serper API — same implementation as ExplorerAgent."""
    api_key = os.environ.get("SERPER_API_KEY", "")
    if not api_key:
        logger.warning("SERPER_API_KEY not set")
        return []
    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "gl": "jp", "hl": "ja", "num": num_results},
        timeout=10,
    )
    resp.raise_for_status()
    results = []
    for item in resp.json().get("organic", [])[:num_results]:
        results.append({
            "title": item.get("title", ""),
            "snippet": item.get("snippet", ""),
            "url": item.get("link", ""),
        })
    return results


class SinglePipeline:
    """Baseline pipeline — one LLM call, no decomposition."""

    def __init__(self, config: RunConfig, persona: Persona):
        self.config = config
        self.persona = persona
        self._agent = SingleAgent()

    def _gather_rag_results(self, user_input: str) -> list[dict]:
        """Run Serper search on user_input keywords — same as ExplorerAgent would."""
        if not self.config.use_rag:
            return []
        try:
            results = _serper_search(user_input, num_results=5)
            logger.info(f"[SinglePipeline] RAG search: {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"[SinglePipeline] Serper failed: {e}")
            return []

    def run(self, user_input: str) -> dict:
        logger.info(f"=== SinglePipeline start: {self.config.run_id} ===")

        # Gather same resources as multi-agent pipeline
        pkg_store = PKGStore(
            persona_id=self.persona.persona_id,
            enabled=self.config.use_pkg,
        )
        rag_results = self._gather_rag_results(user_input)

        state = {
            "user_input": user_input,
            "config": self.config,
            "pkg_store": pkg_store,
            "rag_results": rag_results,
            "timestamp": datetime.now().isoformat(),
        }

        state = self._agent.process(state)

        self._save_logs(state)
        pkg_store.close()
        logger.info(f"=== SinglePipeline complete: {self.config.run_id} ===")
        return state

    def _save_logs(self, state: dict):
        run_dir = RUNS_DIR / self.config.condition / self.config.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Config
        _write_json(run_dir / "config.json", self.config.to_dict())

        # Structured intermediate artifacts (CoT-extracted)
        if "context_raw" in state:
            _write_json(run_dir / "context.json", state["context_raw"])

        if "evidence_raw" in state:
            _write_json(run_dir / "evidence.json", state["evidence_raw"])

        if "hypotheses_raw" in state:
            _write_json(run_dir / "hypotheses.json", state["hypotheses_raw"])

        if "judgements_raw" in state:
            _write_json(run_dir / "judgements.json", state["judgements_raw"])

        if "decision_raw" in state:
            _write_json(run_dir / "decision.json", state["decision_raw"])

        # Final output (same filename as multi-agent for metrics compat)
        raw = state.get("dialogue_raw")
        if raw is not None:
            _write_json(run_dir / "final.json", raw)

        # Plain-text response
        dialogue_output = state.get("dialogue_output")
        if dialogue_output:
            text = dialogue_output.final_response.replace("\\n", "\n")
            (run_dir / "response.txt").write_text(text, encoding="utf-8")

        logger.info(f"Logs saved to {run_dir}")


def _write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
