"""
Condition A — Full (PKG ✓, RAG ✓, Judge ✓)
All modules enabled. Full pipeline of proposed method.

Usage:
    python -m newresearch.run_A                 # All scenarios (S1, S2, S3)
    python -m newresearch.run_A --scenario S1   # Single scenario
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from newresearch.config import make_config
from newresearch.scenarios import SCENARIOS, get_scenario, get_persona
from newresearch.pipeline import Pipeline

CONDITION = "A"
CONDITION_LABEL = "Full (PKG✓ RAG✓ 批評家✓)"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("newresearch")


def run(scenario_id: str, persona):
    """Run one scenario under Condition A."""
    scenario = get_scenario(scenario_id)
    config = make_config(scenario_id, CONDITION, persona.persona_id)

    logger.info(f"Run: {config.run_id}")
    logger.info(f"  Persona  : {persona.persona_id} ({persona.name})")
    logger.info(f"  Scenario : {scenario_id} — {scenario['focus']}")
    logger.info(f"  Condition: {CONDITION} ({CONDITION_LABEL})")

    pipeline = Pipeline(config=config, persona=persona)
    state = pipeline.run(user_input=scenario["user_input"])

    out = state.get("dialogue_output")
    if out:
        print(f"\n{'='*60}")
        print(f"[{CONDITION}] {persona.persona_id} × {scenario_id} — Final Response:")
        print(f"{'='*60}")
        print(out.final_response)
        print(f"{'='*60}\n")

    return state


def main():
    from newresearch.scenarios import PERSONA_IDS
    parser = argparse.ArgumentParser(
        description=f"Condition {CONDITION}: {CONDITION_LABEL}",
    )
    parser.add_argument("--scenario", type=str, default=None,
                        help="Scenario ID (S1..S10). If omitted, run all scenarios")
    parser.add_argument("--persona", type=str, default=None,
                        help="Persona ID (P01, P05, P07). If omitted, run all personas")
    args = parser.parse_args()

    persona_ids = [args.persona] if args.persona else PERSONA_IDS
    scenario_ids = [args.scenario] if args.scenario else list(SCENARIOS.keys())

    for pid in persona_ids:
        persona = get_persona(pid)
        logger.info(f"Persona loaded: {persona.name} ({len(persona.pkg.nodes)} PKG nodes)")
        for sid in scenario_ids:
            logger.info(f"\n{'#'*60}")
            logger.info(f"# {CONDITION} × {pid} × {sid}")
            logger.info(f"{'#'*60}")
            try:
                run(sid, persona)
            except Exception as e:
                logger.error(f"FAILED: {pid} × {sid} × {CONDITION}: {e}", exc_info=True)

    logger.info(f"\nCondition {CONDITION} complete ({len(persona_ids)} personas × {len(scenario_ids)} scenarios)")


if __name__ == "__main__":
    main()
