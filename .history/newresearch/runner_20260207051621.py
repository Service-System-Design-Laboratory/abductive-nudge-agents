"""
Runner — executes the ablation experiment.
Supports 3 personas × 10 scenarios × 4 conditions = 120 runs.
Can also run a subset (e.g., --personas P01 --scenarios S1 S2).
"""
from __future__ import annotations
import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure dotenv is loaded
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from newresearch.config import RunConfig, ABLATION_CONDITIONS, make_config
from newresearch.scenarios import SCENARIOS, PERSONA_IDS, get_scenario, get_persona
from newresearch.pipeline import Pipeline
from newresearch.pipeline_single import SinglePipeline
from newresearch.pkg_store import PKGStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("newresearch")


def run_single(scenario_id: str, condition: str, *, persona=None, persona_id: str = "P01") -> dict:
    """Run a single pipeline (1 persona × 1 scenario × 1 condition).

    Parameters
    ----------
    persona : Persona | None
        If None, load from Neo4J. Pass explicitly to avoid repeated DB calls.
    persona_id : str
        Used when persona is None, or for config labeling.
    """
    if persona is None:
        persona = get_persona(persona_id)
    else:
        persona_id = persona.persona_id

    scenario = get_scenario(scenario_id)
    config = make_config(scenario_id, condition, persona_id)

    logger.info(f"Run: {config.run_id}")
    logger.info(f"  Persona: {persona_id} ({persona.name})")
    logger.info(f"  Scenario: {scenario_id} ({scenario['focus']})")
    logger.info(f"  Condition: {condition} (PKG={config.use_pkg}, RAG={config.use_rag}, 批評家={config.use_judge}, Single={config.is_single})")

    if config.is_single:
        pipeline = SinglePipeline(config=config, persona=persona)
    else:
        pipeline = Pipeline(config=config, persona=persona)
    state = pipeline.run(user_input=scenario["user_input"])

    # Print final response
    dialogue_output = state.get("dialogue_output")
    if dialogue_output:
        print(f"\n{'='*60}")
        print(f"Final Response ({persona_id} × {scenario_id} × {condition}):")
        print(f"{'='*60}")
        print(dialogue_output.final_response)
        print(f"{'='*60}\n")

    return state


def run_all(persona_ids: list[str] | None = None,
            scenario_ids: list[str] | None = None,
            conditions: list[str] | None = None):
    """Run ablation experiments for specified (or all) personas/scenarios/conditions."""
    if persona_ids is None:
        persona_ids = PERSONA_IDS
    if scenario_ids is None:
        scenario_ids = list(SCENARIOS.keys())
    if conditions is None:
        conditions = list(ABLATION_CONDITIONS.keys())

    # Load personas once from Neo4J
    personas = {}
    for pid in persona_ids:
        personas[pid] = get_persona(pid)

    total = len(persona_ids) * len(scenario_ids) * len(conditions)
    logger.info(f"Running {total} experiments ({len(persona_ids)} personas × {len(scenario_ids)} scenarios × {len(conditions)} conditions)")

    # Build set of already-completed runs (date prefix) to skip
    results_base = Path(__file__).parent / "results" / "runs"
    today = __import__("datetime").date.today().isoformat()   # e.g. "2026-02-07"
    cond_suffix = {"A": "PKG1_RAG1_JUDGE1", "B": "PKG0_RAG1_JUDGE1",
                   "C": "PKG1_RAG0_JUDGE1", "D": "SINGLE"}
    done_set: set[tuple[str, str, str]] = set()
    for cond in "ABCD":
        cond_dir = results_base / cond
        if not cond_dir.is_dir():
            continue
        for d in os.listdir(cond_dir):
            if not d.startswith(today):
                continue
            parts = d.split("__")
            if len(parts) >= 3:
                done_set.add((parts[1], parts[2], cond))

    results = []
    n = 0
    skipped = 0
    for pid in persona_ids:
        persona = personas[pid]
        for sid in scenario_ids:
            for cond in conditions:
                n += 1

                # Skip if already completed today
                cond_tag = cond_suffix.get(cond, cond)
                if (pid, sid, cond) in done_set or (pid, cond_tag, cond) in done_set:
                    skipped += 1
                    logger.info(f"SKIP {n}/{total}: {pid} × {sid} × {cond} (already completed)")
                    results.append({
                        "persona_id": pid, "scenario_id": sid,
                        "condition": cond, "status": "skipped",
                    })
                    continue

                logger.info(f"\n{'#'*60}")
                logger.info(f"# Experiment {n}/{total}: {pid} × {sid} × {cond}")
                logger.info(f"{'#'*60}")

                try:
                    # Reset PKG to seed-only state before each run
                    # to prevent cross-run contamination
                    pkg_reset = PKGStore(persona_id=pid, enabled=True, write_enabled=False)
                    pkg_reset.reset_to_seed()
                    pkg_reset.close()

                    state = run_single(sid, cond, persona=persona, persona_id=pid)
                    results.append({
                        "persona_id": pid,
                        "scenario_id": sid,
                        "condition": cond,
                        "run_id": state["config"].run_id,
                        "status": "success",
                    })
                except Exception as e:
                    logger.error(f"FAILED: {pid} × {sid} × {cond}: {e}")
                    results.append({
                        "persona_id": pid,
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
        print(f"  {status} {r['persona_id']} × {r['scenario_id']} × {r['condition']}: {r.get('run_id', r.get('error', ''))}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Abductive Dialogue Pipeline Runner")
    parser.add_argument("--all", action="store_true", help="Run all experiments")
    parser.add_argument("--personas", nargs="+", type=str, help="Persona IDs (P01, P05, P07)")
    parser.add_argument("--scenarios", nargs="+", type=str, help="Scenario IDs (S1..S10)")
    parser.add_argument("--conditions", nargs="+", type=str, help="Conditions (A, B, C, D)")
    parser.add_argument("--scenario", type=str, help="Single scenario ID (legacy)")
    parser.add_argument("--condition", type=str, help="Single condition (legacy)")
    parser.add_argument("--persona", type=str, help="Single persona ID (legacy)")
    args = parser.parse_args()

    if args.all:
        run_all(
            persona_ids=args.personas,
            scenario_ids=args.scenarios,
            conditions=args.conditions,
        )
    elif args.scenario and args.condition:
        pid = args.persona or "P01"
        run_single(args.scenario, args.condition, persona_id=pid)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python -m newresearch.runner --all")
        print("  python -m newresearch.runner --all --personas P01 P05")
        print("  python -m newresearch.runner --all --scenarios S1 S2 S3 --conditions A B")
        print("  python -m newresearch.runner --scenario S1 --condition A --persona P01")


if __name__ == "__main__":
    main()
