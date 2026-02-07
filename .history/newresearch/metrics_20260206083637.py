"""
Metrics extraction — reads all run logs and produces metrics.csv.
"""
from __future__ import annotations
import csv
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("newresearch")

RUNS_DIR = Path(__file__).parent / "results" / "runs"
OUTPUT_CSV = Path(__file__).parent / "results" / "metrics.csv"


def extract_metrics(run_dir: Path) -> dict[str, Any] | None:
    """Extract all metrics from a single run directory."""
    config_path = run_dir / "config.json"
    if not config_path.exists():
        return None

    config = json.loads(config_path.read_text(encoding="utf-8"))
    metrics: dict[str, Any] = {
        "run_id": config.get("run_id", run_dir.name),
        "scenario_id": config.get("scenario_id", ""),
        "condition": config.get("condition", ""),
        "use_pkg": config.get("use_pkg", True),
        "use_rag": config.get("use_rag", True),
        "use_judge": config.get("use_judge", True),
    }

    # ── Hypothesis metrics ─────────────────────────────────────
    hyp_path = run_dir / "hypotheses.json"
    if hyp_path.exists():
        hyp_data = json.loads(hyp_path.read_text(encoding="utf-8"))
        hypotheses = hyp_data.get("hypotheses", [])
        metrics["hypothesis_count"] = len(hypotheses)
        types = [h.get("type", "") for h in hypotheses]
        metrics["type_diversity"] = len(set(types))

        # Abductive structure
        all_explains = []
        total_predictions = 0
        total_disc_q = 0
        total_pkg_refs = 0
        total_ev_refs = 0
        for h in hypotheses:
            all_explains.extend(h.get("explains", []))
            total_predictions += len(h.get("predictions", []))
            total_disc_q += len(h.get("discriminating_questions", []))
            total_pkg_refs += len(h.get("persona_link", []))
            total_ev_refs += len(h.get("evidence_link", []))

        metrics["total_observations_explained"] = len(set(all_explains))
        metrics["avg_predictions_per_h"] = round(total_predictions / max(len(hypotheses), 1), 2)
        metrics["avg_disc_questions_per_h"] = round(total_disc_q / max(len(hypotheses), 1), 2)
        metrics["pkg_ref_count"] = total_pkg_refs
        metrics["evidence_ref_count"] = total_ev_refs
        metrics["evidence_used_ratio"] = round(
            sum(1 for h in hypotheses if h.get("evidence_link")) / max(len(hypotheses), 1), 2
        )
    else:
        for k in ["hypothesis_count", "type_diversity", "total_observations_explained",
                   "avg_predictions_per_h", "avg_disc_questions_per_h",
                   "pkg_ref_count", "evidence_ref_count", "evidence_used_ratio"]:
            metrics[k] = None

    # ── Judge metrics ──────────────────────────────────────────
    judge_path = run_dir / "judgements.json"
    decision_path = run_dir / "decision.json"

    if judge_path.exists() and decision_path.exists():
        judge_data = json.loads(judge_path.read_text(encoding="utf-8"))
        decision_data = json.loads(decision_path.read_text(encoding="utf-8"))
        judgements = judge_data.get("judgements", [])
        selected_id = decision_data.get("selected_hypothesis_id", "")

        if judgements:
            # Score per hypothesis
            scores_by_id = {}
            for j in judgements:
                s = j.get("scores", {})
                total = sum(s.get(k, 0) for k in ["explanatory_power", "consistency",
                                                    "persona_alignment", "evidence_reliability"])
                scores_by_id[j["hypothesis_id"]] = {
                    "total": total,
                    "persona_alignment": s.get("persona_alignment", 0),
                    **s,
                }

            # Selected vs non-selected
            selected_score = scores_by_id.get(selected_id, {}).get("total", 0)
            non_selected = [v["total"] for k, v in scores_by_id.items() if k != selected_id]
            avg_non_selected = round(sum(non_selected) / max(len(non_selected), 1), 2)

            metrics["selected_total_score"] = selected_score
            metrics["avg_non_selected_score"] = avg_non_selected
            metrics["score_gap"] = round(selected_score - avg_non_selected, 2)

            # Did top-total get selected?
            max_total_id = max(scores_by_id, key=lambda k: scores_by_id[k]["total"])
            metrics["top_total_selected"] = 1 if max_total_id == selected_id else 0

            # Did top-persona get selected?
            max_persona_id = max(scores_by_id, key=lambda k: scores_by_id[k]["persona_alignment"])
            metrics["top_persona_selected"] = 1 if max_persona_id == selected_id else 0

            # Average 4 axis scores
            for axis in ["explanatory_power", "consistency", "persona_alignment", "evidence_reliability"]:
                vals = [scores_by_id[k][axis] for k in scores_by_id]
                metrics[f"avg_{axis}"] = round(sum(vals) / len(vals), 2)
        else:
            for k in ["selected_total_score", "avg_non_selected_score", "score_gap",
                       "top_total_selected", "top_persona_selected",
                       "avg_explanatory_power", "avg_consistency",
                       "avg_persona_alignment", "avg_evidence_reliability"]:
                metrics[k] = None
    else:
        for k in ["selected_total_score", "avg_non_selected_score", "score_gap",
                   "top_total_selected", "top_persona_selected",
                   "avg_explanatory_power", "avg_consistency",
                   "avg_persona_alignment", "avg_evidence_reliability"]:
            metrics[k] = None

    # ── Empathy / Nudge metrics ────────────────────────────────
    final_path = run_dir / "final.json"
    if final_path.exists():
        final_data = json.loads(final_path.read_text(encoding="utf-8"))
        markers = final_data.get("markers", {})
        empathy = markers.get("empathy", {})
        nudge = markers.get("nudge", {})

        metrics["empathy_acknowledgement"] = 1 if empathy.get("acknowledgement") else 0
        metrics["empathy_reflection"] = 1 if empathy.get("reflection") else 0
        metrics["empathy_perspective_prompt"] = 1 if empathy.get("perspective_prompt") else 0
        metrics["empathy_count"] = sum([
            metrics["empathy_acknowledgement"],
            metrics["empathy_reflection"],
            metrics["empathy_perspective_prompt"],
        ])

        metrics["nudge_has_question"] = 1 if nudge.get("has_question") else 0
        metrics["nudge_has_options"] = 1 if nudge.get("has_options") else 0
        metrics["nudge_has_small_action"] = 1 if nudge.get("has_small_action") else 0
        metrics["nudge_count"] = sum([
            metrics["nudge_has_question"],
            metrics["nudge_has_options"],
            metrics["nudge_has_small_action"],
        ])
        metrics["directive_level"] = nudge.get("directive_level", "")
    else:
        for k in ["empathy_acknowledgement", "empathy_reflection", "empathy_perspective_prompt",
                   "empathy_count", "nudge_has_question", "nudge_has_options",
                   "nudge_has_small_action", "nudge_count", "directive_level"]:
            metrics[k] = None

    return metrics


def collect_all_metrics() -> list[dict]:
    """Collect metrics from all run directories."""
    if not RUNS_DIR.exists():
        logger.warning(f"Runs directory not found: {RUNS_DIR}")
        return []

    all_metrics = []
    for run_dir in sorted(RUNS_DIR.iterdir()):
        if run_dir.is_dir():
            m = extract_metrics(run_dir)
            if m:
                all_metrics.append(m)

    return all_metrics


def save_csv(metrics: list[dict], output_path: Path | None = None):
    """Save metrics to CSV."""
    if not metrics:
        logger.warning("No metrics to save")
        return

    path = output_path or OUTPUT_CSV
    fieldnames = list(metrics[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(metrics)

    logger.info(f"Metrics saved to {path} ({len(metrics)} runs)")


def main():
    logging.basicConfig(level=logging.INFO)
    metrics = collect_all_metrics()
    if metrics:
        save_csv(metrics)
        print(f"\n{'='*60}")
        print(f"Collected metrics from {len(metrics)} runs → {OUTPUT_CSV}")
        print(f"{'='*60}")

        # Quick summary
        for m in metrics:
            print(f"  {m['scenario_id']} × {m['condition']}: "
                  f"H={m.get('hypothesis_count','?')}, "
                  f"type_div={m.get('type_diversity','?')}, "
                  f"empathy={m.get('empathy_count','?')}, "
                  f"nudge={m.get('nudge_count','?')}")
    else:
        print("No run data found. Execute `python -m newresearch.runner --all` first.")


if __name__ == "__main__":
    main()
