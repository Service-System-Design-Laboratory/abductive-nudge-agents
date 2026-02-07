"""
Runner — executes the 12-run ablation experiment (3 scenarios × 4 conditions).
"""
from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

# Ensure dotenv is loaded
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from newresearch.config import RunConfig, ABLATION_CONDITIONS, make_config
from newresearch.scenarios import SCENARIOS, get_scenario, get_persona
from newresearch.pipeline import Pipeline
from newresearch.pipeline_single import SinglePipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("newresearch")


def run_single(scenario_id: str, condition: str, *, persona=None) -> dict:
    """Run a single pipeline (1 scenario × 1 condition).

    Parameters
    ----------
    persona : Persona | None
        If None, load from Neo4J. Pass explicitly to avoid repeated DB calls.
    """
    if persona is None:
        persona = get_persona()

    scenario = get_scenario(scenario_id)
    config = make_config(scenario_id, condition)

    logger.info(f"Run: {config.run_id}")
    logger.info(f"  Scenario: {scenario_id} ({scenario['focus']})")
    logger.info(f"  Condition: {condition} (PKG={config.use_pkg}, RAG={config.use_rag}, 批評家={config.use_judge})")

    pipeline = Pipeline(config=config, persona=persona)
    state = pipeline.run(user_input=scenario["user_input"])

    # Print final response
    dialogue_output = state.get("dialogue_output")
    if dialogue_output:
        print(f"\n{'='*60}")
        print(f"Final Response ({scenario_id} × {condition}):")
        print(f"{'='*60}")
        print(dialogue_output.final_response)
        print(f"{'='*60}\n")

    return state


def run_all():
    """Run all 12 ablation experiments."""
    scenario_ids = list(SCENARIOS.keys())
    conditions = list(ABLATION_CONDITIONS.keys())

    # Load persona once from Neo4J
    persona = get_persona()

    total = len(scenario_ids) * len(conditions)
    logger.info(f"Running {total} experiments ({len(scenario_ids)} scenarios × {len(conditions)} conditions)")

    results = []
    for i, sid in enumerate(scenario_ids):
        for j, cond in enumerate(conditions):
            n = i * len(conditions) + j + 1
            logger.info(f"\n{'#'*60}")
            logger.info(f"# Experiment {n}/{total}: {sid} × {cond}")
            logger.info(f"{'#'*60}")

            try:
                state = run_single(sid, cond, persona=persona)
                results.append({
                    "scenario_id": sid,
                    "condition": cond,
                    "run_id": state["config"].run_id,
                    "status": "success",
                })
            except Exception as e:
                logger.error(f"FAILED: {sid} × {cond}: {e}")
                results.append({
                    "scenario_id": sid,
                    "condition": cond,
                    "status": "failed",
                    "error": str(e),
                })

    # Summary
    print(f"\n{'='*60}")
    print("Experiment Summary")
    print(f"{'='*60}")
    success = sum(1 for r in results if r["status"] == "success")
    print(f"Success: {success}/{total}")
    for r in results:
        status = "✅" if r["status"] == "success" else "❌"
        print(f"  {status} {r['scenario_id']} × {r['condition']}: {r.get('run_id', r.get('error', ''))}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Abductive Dialogue Pipeline Runner")
    parser.add_argument("--all", action="store_true", help="Run all 12 experiments")
    parser.add_argument("--scenario", type=str, help="Scenario ID (S1, S2, S3)")
    parser.add_argument("--condition", type=str, help="Condition (A, B, C, D)")
    args = parser.parse_args()

    if args.all:
        run_all()
    elif args.scenario and args.condition:
        run_single(args.scenario, args.condition)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python -m newresearch.runner --all")
        print("  python -m newresearch.runner --scenario S1 --condition A")


if __name__ == "__main__":
    main()
