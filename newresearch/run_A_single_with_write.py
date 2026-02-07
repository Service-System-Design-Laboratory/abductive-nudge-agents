"""
Run ONE scenario of Condition A with PKG write_enabled=True.
After execution, Neo4j will contain the full reasoning graph:
  seed PKG nodes → Observation → Hypothesis → Judgement → Decision

Usage:
    python -m newresearch.run_A_single_with_write
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from newresearch.config import make_config
from newresearch.scenarios import get_scenario, get_persona
from newresearch.pkg_store import PKGStore
from newresearch.pipeline import Pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("newresearch")

CONDITION = "A"
PERSONA_ID = "P01"
SCENARIO_ID = "S1"


def main():
    persona = get_persona(PERSONA_ID)
    scenario = get_scenario(SCENARIO_ID)
    config = make_config(SCENARIO_ID, CONDITION, PERSONA_ID)

    logger.info(f"=== PKG Write-Enabled Demo Run ===")
    logger.info(f"  Persona  : {PERSONA_ID} ({persona.name})")
    logger.info(f"  Scenario : {SCENARIO_ID} — {scenario['focus']}")
    logger.info(f"  Condition: {CONDITION} (Full)")
    logger.info(f"  Run ID   : {config.run_id}")

    # --- Override: create PKGStore with write_enabled=True ---
    pkg_store = PKGStore(
        persona_id=persona.persona_id,
        enabled=config.use_pkg,
        write_enabled=True,           # ★ Neo4j に書き込む
    )

    # Count seed nodes before run
    pre_count = _count_nodes(pkg_store)
    logger.info(f"  PKG nodes before run: {pre_count}")

    # Monkey-patch Pipeline.run to use our write-enabled PKGStore
    pipeline = Pipeline(config=config, persona=persona)

    state = {
        "user_input": scenario["user_input"],
        "config": config,
        "pkg_store": pkg_store,
        "timestamp": datetime.now().isoformat(),
    }

    # Run agents in order (same as Pipeline.run but using our state)
    agent_order = ["context", "explorer", "hypothesis", "judge", "decision", "dialogue"]
    for agent_name in agent_order:
        agent = pipeline._agents[agent_name]
        logger.info(f"--- {agent.name} ---")
        state = agent.process(state)

    pipeline._save_logs(state)

    # Count nodes after run
    post_count = _count_nodes(pkg_store)
    logger.info(f"\n  PKG nodes after run: {post_count}  (+{post_count - pre_count} new)")

    pkg_store.close()

    # Print final response
    out = state.get("dialogue_output")
    if out:
        print(f"\n{'='*60}")
        print(f"Final Response:")
        print(f"{'='*60}")
        print(out.final_response)
        print(f"{'='*60}")

    print(f"\n★ Neo4j Browser で PKG を確認できます:")
    print(f"  http://localhost:7474")
    print(f"  Cypher: MATCH (u:ExpUser {{persona_id: '{PERSONA_ID}'}})-[*1..3]-(n) RETURN u, n")
    print(f"  または: MATCH (n) RETURN n  (全ノード表示)")


def _count_nodes(pkg_store: PKGStore) -> int:
    if not pkg_store._driver:
        return 0
    with pkg_store._driver.session() as s:
        result = s.run(
            "MATCH (n) WHERE n.persona_id = $pid OR (n:ExpUser AND n.persona_id = $pid) RETURN count(n) AS c",
            pid=pkg_store.persona_id,
        )
        return result.single()["c"]


if __name__ == "__main__":
    main()
