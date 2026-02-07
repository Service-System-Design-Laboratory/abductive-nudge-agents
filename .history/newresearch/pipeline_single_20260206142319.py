"""
SinglePipeline — minimal pipeline for Condition D (Single Agent baseline).
Runs only the SingleAgent (1 LLM call) and saves results in the same
directory structure as the multi-agent pipeline for metrics compatibility.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path

from newresearch.config import RunConfig
from newresearch.schemas import Persona
from newresearch.agents.single import SingleAgent

logger = logging.getLogger("newresearch")

RUNS_DIR = Path(__file__).parent / "results" / "runs"


class SinglePipeline:
    """Baseline pipeline — one LLM call, no decomposition."""

    def __init__(self, config: RunConfig, persona: Persona):
        self.config = config
        self.persona = persona
        self._agent = SingleAgent()

    def run(self, user_input: str) -> dict:
        logger.info(f"=== SinglePipeline start: {self.config.run_id} ===")

        state = {
            "user_input": user_input,
            "config": self.config,
            "persona_summary": self.persona.summary,
            "timestamp": datetime.now().isoformat(),
        }

        state = self._agent.process(state)

        self._save_logs(state)
        logger.info(f"=== SinglePipeline complete: {self.config.run_id} ===")
        return state

    def _save_logs(self, state: dict):
        run_dir = RUNS_DIR / self.config.condition / self.config.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Config
        _write_json(run_dir / "config.json", self.config.to_dict())

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
