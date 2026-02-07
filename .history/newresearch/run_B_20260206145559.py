"""
Condition B — −PKG (PKG ✗, RAG ✓, 批評家 ✓)
PKGを無効化し、ユーザ知識グラフなしで対話を生成。

Usage:
    python -m newresearch.run_B                 # 全シナリオ (S1, S2, S3)
    python -m newresearch.run_B --scenario S1   # 単一シナリオ
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

CONDITION = "B"
CONDITION_LABEL = "−PKG (PKG✗ RAG✓ 批評家✓)"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("newresearch")


def run(scenario_id: str, persona):
    """Run one scenario under Condition B."""
    scenario = get_scenario(scenario_id)
    config = make_config(scenario_id, CONDITION)

    logger.info(f"Run: {config.run_id}")
    logger.info(f"  Scenario : {scenario_id} — {scenario['focus']}")
    logger.info(f"  Condition: {CONDITION} ({CONDITION_LABEL})")

    pipeline = Pipeline(config=config, persona=persona)
    state = pipeline.run(user_input=scenario["user_input"])

    out = state.get("dialogue_output")
    if out:
        print(f"\n{'='*60}")
        print(f"[{CONDITION}] {scenario_id} — Final Response:")
        print(f"{'='*60}")
        print(out.final_response)
        print(f"{'='*60}\n")

    return state


def main():
    parser = argparse.ArgumentParser(
        description=f"Condition {CONDITION}: {CONDITION_LABEL}",
    )
    parser.add_argument("--scenario", type=str, default=None,
                        help="Scenario ID (S1, S2, S3). 省略時は全シナリオ実行")
    args = parser.parse_args()

    persona = get_persona()  # Neo4J から一度だけ読み込み
    logger.info(f"Persona loaded: {persona.name} ({len(persona.pkg.nodes)} PKG nodes)")

    scenario_ids = [args.scenario] if args.scenario else list(SCENARIOS.keys())

    for sid in scenario_ids:
        logger.info(f"\n{'#'*60}")
        logger.info(f"# {CONDITION} × {sid}")
        logger.info(f"{'#'*60}")
        try:
            run(sid, persona)
        except Exception as e:
            logger.error(f"FAILED: {sid} × {CONDITION}: {e}", exc_info=True)

    logger.info(f"\nCondition {CONDITION} complete ({len(scenario_ids)} scenarios)")


if __name__ == "__main__":
    main()
