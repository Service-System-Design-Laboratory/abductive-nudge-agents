"""
Metrics extraction — reads all run logs and produces metrics.csv.

Metric design principles (2026-02-06 rev):
  - Avoid metrics that merely measure prompt-compliance (type_diversity, nudge_count)
  - Focus on metrics where ablation conditions produce natural variance
  - New core metrics:
      persona_link_count / evidence_link_count  (content-grounding)
      observation_coverage                       (explanatory breadth)
      top_total_selected / fatal_flaw_avoided    (Judge effectiveness)
      response_length / option_specificity       (Nudge quality)
"""
from __future__ import annotations
import csv
import json
import logging
import re
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

    # ── Context metrics ────────────────────────────────────────
    ctx_path = run_dir / "context.json"
    total_observations = 0
    if ctx_path.exists():
        ctx_data = json.loads(ctx_path.read_text(encoding="utf-8"))
        observations = ctx_data.get("observations", [])
        total_observations = len(observations)
        metrics["observation_count"] = total_observations
    else:
        metrics["observation_count"] = None

    # ── Hypothesis metrics ─────────────────────────────────────
    hyp_path = run_dir / "hypotheses.json"
    if hyp_path.exists():
        hyp_data = json.loads(hyp_path.read_text(encoding="utf-8"))
        hypotheses = hyp_data.get("hypotheses", [])
        metrics["hypothesis_count"] = len(hypotheses)

        # Type diversity (kept for reference, but no longer primary)
        types = [h.get("type", "") for h in hypotheses]
        metrics["type_diversity"] = len(set(types))
        metrics["type_counts"] = len(types)  # H count for ratio

        # ── NEW: Content-grounding metrics ─────────────────────
        all_explains: set[str] = set()
        total_predictions = 0
        total_disc_q = 0
        persona_links_all: list[str] = []
        evidence_links_all: list[str] = []
        h_with_persona = 0
        h_with_evidence = 0

        for h in hypotheses:
            explains = h.get("explains", [])
            all_explains.update(explains)
            total_predictions += len(h.get("predictions", []))
            total_disc_q += len(h.get("discriminating_questions", []))

            plinks = h.get("persona_link", [])
            elinks = h.get("evidence_link", [])
            persona_links_all.extend(plinks)
            evidence_links_all.extend(elinks)
            if plinks:
                h_with_persona += 1
            if elinks:
                h_with_evidence += 1

        n_h = max(len(hypotheses), 1)

        # Observation coverage: fraction of O's explained by at least one H
        if total_observations > 0:
            metrics["observation_coverage"] = round(len(all_explains) / total_observations, 2)
        else:
            metrics["observation_coverage"] = None

        metrics["total_observations_explained"] = len(all_explains)
        metrics["avg_predictions_per_h"] = round(total_predictions / n_h, 2)
        metrics["avg_disc_questions_per_h"] = round(total_disc_q / n_h, 2)

        # Content-grounding: PKG and evidence link counts
        metrics["persona_link_count"] = len(persona_links_all)
        metrics["persona_link_unique"] = len(set(persona_links_all))
        metrics["persona_link_per_h"] = round(len(persona_links_all) / n_h, 2)
        metrics["h_with_persona_ratio"] = round(h_with_persona / n_h, 2)

        metrics["evidence_link_count"] = len(evidence_links_all)
        metrics["evidence_link_unique"] = len(set(evidence_links_all))
        metrics["evidence_link_per_h"] = round(len(evidence_links_all) / n_h, 2)
        metrics["h_with_evidence_ratio"] = round(h_with_evidence / n_h, 2)
    else:
        for k in ["hypothesis_count", "type_diversity", "type_counts",
                   "observation_coverage", "total_observations_explained",
                   "avg_predictions_per_h", "avg_disc_questions_per_h",
                   "persona_link_count", "persona_link_unique", "persona_link_per_h",
                   "h_with_persona_ratio",
                   "evidence_link_count", "evidence_link_unique", "evidence_link_per_h",
                   "h_with_evidence_ratio"]:
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
            scores_by_id: dict[str, dict] = {}
            for j in judgements:
                s = j.get("scores", {})
                total = sum(s.get(k, 0) for k in ["explanatory_power", "consistency",
                                                    "persona_alignment", "evidence_reliability"])
                scores_by_id[j["hypothesis_id"]] = {
                    "total": total,
                    "fatal_flaws": j.get("fatal_flaws", []),
                    **s,
                }

            # Selected score
            selected_score = scores_by_id.get(selected_id, {}).get("total", 0)
            non_selected = [v["total"] for k, v in scores_by_id.items() if k != selected_id]
            avg_non_selected = round(sum(non_selected) / max(len(non_selected), 1), 2)

            metrics["selected_total_score"] = selected_score
            metrics["avg_non_selected_score"] = avg_non_selected
            metrics["score_gap"] = round(selected_score - avg_non_selected, 2)

            # ── NEW: Judge effectiveness ───────────────────────
            # top_total_selected: did Decision pick the highest-scored H?
            max_total_id = max(scores_by_id, key=lambda k: scores_by_id[k]["total"])
            metrics["top_total_selected"] = 1 if max_total_id == selected_id else 0

            # top_persona_selected: was the best persona-aligned H picked?
            max_persona_id = max(scores_by_id, key=lambda k: scores_by_id[k].get("persona_alignment", 0))
            metrics["top_persona_selected"] = 1 if max_persona_id == selected_id else 0

            # fatal_flaw_avoided: selected H has no fatal flaws
            selected_flaws = scores_by_id.get(selected_id, {}).get("fatal_flaws", [])
            metrics["fatal_flaw_avoided"] = 1 if not selected_flaws else 0

            # How many Hs had fatal flaws?
            fatal_count = sum(1 for v in scores_by_id.values() if v.get("fatal_flaws"))
            metrics["fatal_flaw_h_count"] = fatal_count

            # Axis averages
            for axis in ["explanatory_power", "consistency", "persona_alignment", "evidence_reliability"]:
                vals = [scores_by_id[k][axis] for k in scores_by_id if axis in scores_by_id[k]]
                metrics[f"avg_{axis}"] = round(sum(vals) / max(len(vals), 1), 2)
        else:
            _null_judge(metrics)
    else:
        _null_judge(metrics)

    # ── Empathy / Nudge metrics ────────────────────────────────
    final_path = run_dir / "final.json"
    if final_path.exists():
        final_data = json.loads(final_path.read_text(encoding="utf-8"))
        markers = final_data.get("markers", {})
        empathy = markers.get("empathy", {})
        nudge = markers.get("nudge", {})

        # Empathy sub-markers
        metrics["empathy_acknowledgement"] = 1 if empathy.get("acknowledgement") else 0
        metrics["empathy_reflection"] = 1 if empathy.get("reflection") else 0
        metrics["empathy_perspective_prompt"] = 1 if empathy.get("perspective_prompt") else 0
        metrics["empathy_count"] = sum([
            metrics["empathy_acknowledgement"],
            metrics["empathy_reflection"],
            metrics["empathy_perspective_prompt"],
        ])

        # Nudge sub-markers (kept for compliance check)
        metrics["nudge_has_question"] = 1 if nudge.get("has_question") else 0
        metrics["nudge_has_options"] = 1 if nudge.get("has_options") else 0
        metrics["nudge_has_small_action"] = 1 if nudge.get("has_small_action") else 0
        metrics["nudge_count"] = sum([
            metrics["nudge_has_question"],
            metrics["nudge_has_options"],
            metrics["nudge_has_small_action"],
        ])
        metrics["directive_level"] = nudge.get("directive_level", "")

        # ── NEW: Nudge quality metrics ─────────────────────────
        response_text = final_data.get("final_response", "")
        metrics["response_length"] = len(response_text)

        # Option specificity: count of named entities / specific terms in options
        # Proxy: average character length of option-like sentences (lines with 1. 2. etc.)
        option_lines = re.findall(r'[1-9][.．].*', response_text)
        if option_lines:
            metrics["option_count"] = len(option_lines)
            avg_opt_len = round(sum(len(l) for l in option_lines) / len(option_lines), 1)
            metrics["option_avg_length"] = avg_opt_len
        else:
            metrics["option_count"] = 0
            metrics["option_avg_length"] = 0
    else:
        for k in ["empathy_acknowledgement", "empathy_reflection", "empathy_perspective_prompt",
                   "empathy_count", "nudge_has_question", "nudge_has_options",
                   "nudge_has_small_action", "nudge_count", "directive_level",
                   "response_length", "option_count", "option_avg_length"]:
            metrics[k] = None

    return metrics


def _null_judge(metrics: dict):
    """Set all judge-related metrics to None."""
    for k in ["selected_total_score", "avg_non_selected_score", "score_gap",
               "top_total_selected", "top_persona_selected",
               "fatal_flaw_avoided", "fatal_flaw_h_count",
               "avg_explanatory_power", "avg_consistency",
               "avg_persona_alignment", "avg_evidence_reliability"]:
        metrics[k] = None


def collect_all_metrics() -> list[dict]:
    """Collect metrics from all run directories (supports condition sub-dirs)."""
    if not RUNS_DIR.exists():
        logger.warning(f"Runs directory not found: {RUNS_DIR}")
        return []

    all_metrics = []
    # Support both flat (runs/{run_id}) and nested (runs/{condition}/{run_id})
    for entry in sorted(RUNS_DIR.iterdir()):
        if not entry.is_dir():
            continue
        # Check if this dir itself is a run (has config.json)
        if (entry / "config.json").exists():
            m = extract_metrics(entry)
            if m:
                all_metrics.append(m)
        else:
            # Condition sub-directory — iterate its children
            for run_dir in sorted(entry.iterdir()):
                if run_dir.is_dir() and (run_dir / "config.json").exists():
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

        # Quick summary — show metrics that actually vary across conditions
        for m in metrics:
            print(f"  {m['scenario_id']} × {m['condition']}: "
                  f"pkg_link={m.get('persona_link_count','?')}, "
                  f"ev_link={m.get('evidence_link_count','?')}, "
                  f"obs_cov={m.get('observation_coverage','?')}, "
                  f"top_sel={m.get('top_total_selected','?')}, "
                  f"fatal_ok={m.get('fatal_flaw_avoided','?')}, "
                  f"resp_len={m.get('response_length','?')}"
                  )
    else:
        print("No run data found. Execute `python -m newresearch.runner --all` first.")


if __name__ == "__main__":
    main()
