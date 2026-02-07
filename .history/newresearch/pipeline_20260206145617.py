"""
Pipeline orchestrator — runs all 6 agents in sequence and saves logs.
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from newresearch.config import RunConfig
from newresearch.schemas import Persona
from newresearch.agents.context import ContextAgent
from newresearch.agents.explorer import ExplorerAgent
from newresearch.agents.hypothesis import HypothesisAgent
from newresearch.agents.judge import JudgeAgent
from newresearch.agents.decision import DecisionAgent
from newresearch.agents.dialogue import DialogueAgent

logger = logging.getLogger("newresearch")

RUNS_DIR = Path(__file__).parent / "results" / "runs"


class Pipeline:
    """End-to-end abductive dialogue pipeline."""

    def __init__(self, config: RunConfig, persona: Persona):
        self.config = config
        self.persona = persona
        self._agents = {
            "context": ContextAgent(),
            "explorer": ExplorerAgent(),
            "hypothesis": HypothesisAgent(),
            "judge": JudgeAgent(),
            "decision": DecisionAgent(),
            "dialogue": DialogueAgent(),
        }

    def run(self, user_input: str) -> dict:
        """Execute the full pipeline and return the final state."""
        logger.info(f"=== Pipeline start: {self.config.run_id} ===")

        # Build initial state
        state = {
            "user_input": user_input,
            "config": self.config,
            "pkg_summary": self.persona.pkg.to_graph_text() if self.config.use_pkg else "",
            "timestamp": datetime.now().isoformat(),
        }

        # Agent execution order
        agent_order = ["context", "explorer", "hypothesis", "judge", "decision", "dialogue"]

        pipeline_log = []
        for agent_name in agent_order:
            agent = self._agents[agent_name]
            logger.info(f"--- {agent.name} ---")

            try:
                state = agent.process(state)
                # Capture raw output for logging
                raw_key = f"{agent_name}_raw"
                pipeline_log.append({
                    "agent": agent.name,
                    "output": state.get(raw_key),
                    "skipped": state.get(raw_key) is None,
                })
            except Exception as e:
                logger.error(f"[{agent.name}] Error: {e}")
                pipeline_log.append({
                    "agent": agent.name,
                    "error": str(e),
                    "skipped": False,
                })
                raise

        state["pipeline_log"] = pipeline_log
        self._save_logs(state)
        logger.info(f"=== Pipeline complete: {self.config.run_id} ===")
        return state

    def _save_logs(self, state: dict):
        """Save all agent outputs as individual JSON files."""
        run_dir = RUNS_DIR / self.config.condition / self.config.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        # Config
        _write_json(run_dir / "config.json", self.config.to_dict())

        # Agent outputs
        for key, filename in [
            ("context_raw", "context.json"),
            ("explorer_raw", "evidence.json"),
            ("hypothesis_raw", "hypotheses.json"),
            ("judge_raw", "judgements.json"),
            ("decision_raw", "decision.json"),
            ("dialogue_raw", "final.json"),
        ]:
            data = state.get(key)
            if data is not None:
                _write_json(run_dir / filename, data)

        # Also save final response as plain text for easy reading
        dialogue_output = state.get("dialogue_output")
        if dialogue_output:
            # Expand literal \n sequences to actual newlines
            text = dialogue_output.final_response.replace("\\n", "\n")
            (run_dir / "response.txt").write_text(text, encoding="utf-8")

        logger.info(f"Logs saved to {run_dir}")


def _write_json(path: Path, data: dict):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
