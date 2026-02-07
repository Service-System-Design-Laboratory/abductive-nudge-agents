"""
Visualization — generates figures from metrics.csv for the paper.
"""
from __future__ import annotations
import csv
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

logger = logging.getLogger("newresearch")

METRICS_CSV = Path(__file__).parent / "results" / "metrics.csv"
FIGURES_DIR = Path(__file__).parent / "results" / "figures"

# ── Japanese font setup ────────────────────────────────────────────
def _setup_japanese_font():
    """Try to use a Japanese font if available."""
    # Prefer CJK fonts that actually support Latin + Japanese glyphs
    jp_fonts = []
    for f in fm.findSystemFonts():
        fname = f.lower()
        if any(k in fname for k in ["notosanscjk", "notosansjp", "ipag", "ipam", "ipagothic", "ipamincho"]):
            jp_fonts.append(f)
    if jp_fonts:
        plt.rcParams["font.family"] = fm.FontProperties(fname=jp_fonts[0]).get_name()
    else:
        # Fallback: use DejaVu Sans (no Japanese, but all Latin glyphs work)
        plt.rcParams["font.family"] = "DejaVu Sans"


def load_metrics() -> list[dict]:
    if not METRICS_CSV.exists():
        raise FileNotFoundError(f"{METRICS_CSV} not found. Run `python -m newresearch.metrics` first.")
    with open(METRICS_CSV, encoding="utf-8") as f:
        return list(csv.DictReader(f))


CONDITION_LABELS = {"A": "Full", "B": "−PKG", "C": "−RAG", "D": "−Judge"}
CONDITION_COLORS = {"A": "#4C72B0", "B": "#DD8452", "C": "#55A868", "D": "#C44E52"}


def fig_a_judge_scores(metrics: list[dict]):
    """Fig. A: Selected vs non-selected Judge scores (4 axes)."""
    _setup_japanese_font()

    # Only conditions with judge (A, B, C)
    rows = [m for m in metrics if m.get("avg_explanatory_power")]
    if not rows:
        logger.warning("No judge data for Fig A")
        return

    axes = ["explanatory_power", "consistency", "persona_alignment", "evidence_reliability"]
    conditions = sorted(set(r["condition"] for r in rows))

    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(axes))
    width = 0.2
    offsets = np.linspace(-width, width, len(conditions))

    for i, cond in enumerate(conditions):
        cond_rows = [r for r in rows if r["condition"] == cond]
        means = []
        for axis in axes:
            vals = [float(r.get(f"avg_{axis}", 0)) for r in cond_rows]
            means.append(np.mean(vals) if vals else 0)
        ax.bar(x + offsets[i], means, width * 0.9,
               label=CONDITION_LABELS.get(cond, cond),
               color=CONDITION_COLORS.get(cond, "#999"))

    ax.set_xlabel("Evaluation Axis")
    ax.set_ylabel("Average Score (1-5)")
    ax.set_title("Fig. A: Judge Scores by Condition")
    ax.set_xticks(x)
    ax.set_xticklabels(["Explanatory\nPower", "Consistency", "Persona\nAlignment", "Evidence\nReliability"])
    ax.legend()
    ax.set_ylim(0, 5.5)
    ax.grid(axis="y", alpha=0.3)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "fig_a_judge_scores.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved fig_a_judge_scores.png")


def fig_b_type_diversity(metrics: list[dict]):
    """Fig. B: Hypothesis type diversity by condition."""
    _setup_japanese_font()

    conditions = sorted(set(m["condition"] for m in metrics))
    fig, ax = plt.subplots(figsize=(8, 5))

    for cond in conditions:
        cond_rows = [m for m in metrics if m["condition"] == cond]
        diversities = [int(m.get("type_diversity", 0)) for m in cond_rows]
        scenarios = [m["scenario_id"] for m in cond_rows]

        x_pos = [list(CONDITION_LABELS.keys()).index(cond)]
        ax.bar(x_pos, [np.mean(diversities)], 0.6,
               label=CONDITION_LABELS.get(cond, cond),
               color=CONDITION_COLORS.get(cond, "#999"))
        # Scatter individual points
        for d in diversities:
            ax.scatter(x_pos[0] + np.random.uniform(-0.15, 0.15), d,
                       color="black", s=30, zorder=5, alpha=0.6)

    ax.set_xlabel("Condition")
    ax.set_ylabel("Type Diversity (unique types)")
    ax.set_title("Fig. B: Hypothesis Type Diversity by Condition")
    ax.set_xticks(range(len(conditions)))
    ax.set_xticklabels([CONDITION_LABELS.get(c, c) for c in conditions])
    ax.set_ylim(0, 6)
    ax.grid(axis="y", alpha=0.3)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "fig_b_type_diversity.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved fig_b_type_diversity.png")


def fig_c_empathy_nudge(metrics: list[dict]):
    """Fig. C: Empathy/Nudge marker rates by condition."""
    _setup_japanese_font()

    conditions = sorted(set(m["condition"] for m in metrics))
    empathy_keys = ["empathy_acknowledgement", "empathy_reflection", "empathy_perspective_prompt"]
    nudge_keys = ["nudge_has_question", "nudge_has_options", "nudge_has_small_action"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Empathy
    x = np.arange(len(empathy_keys))
    width = 0.18
    offsets = np.linspace(-width * 1.5, width * 1.5, len(conditions))
    for i, cond in enumerate(conditions):
        cond_rows = [m for m in metrics if m["condition"] == cond]
        rates = []
        for key in empathy_keys:
            vals = [int(m.get(key, 0)) for m in cond_rows]
            rates.append(np.mean(vals) if vals else 0)
        ax1.bar(x + offsets[i], rates, width * 0.9,
                label=CONDITION_LABELS.get(cond, cond),
                color=CONDITION_COLORS.get(cond, "#999"))

    ax1.set_title("Empathy Markers")
    ax1.set_xticks(x)
    ax1.set_xticklabels(["Acknowledgement", "Reflection", "Perspective\nPrompt"])
    ax1.set_ylim(0, 1.2)
    ax1.set_ylabel("Rate")
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    # Nudge
    x = np.arange(len(nudge_keys))
    for i, cond in enumerate(conditions):
        cond_rows = [m for m in metrics if m["condition"] == cond]
        rates = []
        for key in nudge_keys:
            vals = [int(m.get(key, 0)) for m in cond_rows]
            rates.append(np.mean(vals) if vals else 0)
        ax2.bar(x + offsets[i], rates, width * 0.9,
                label=CONDITION_LABELS.get(cond, cond),
                color=CONDITION_COLORS.get(cond, "#999"))

    ax2.set_title("Nudge Markers")
    ax2.set_xticks(x)
    ax2.set_xticklabels(["Question", "Options", "Small Action"])
    ax2.set_ylim(0, 1.2)
    ax2.set_ylabel("Rate")
    ax2.legend()
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("Fig. C: Empathy & Nudge Marker Rates by Condition", fontsize=13)
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "fig_c_empathy_nudge.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved fig_c_empathy_nudge.png")


def fig_d_summary_table(metrics: list[dict]):
    """Fig. D: Per-run summary table."""
    _setup_japanese_font()

    cols = ["scenario_id", "condition", "hypothesis_count", "type_diversity",
            "score_gap", "empathy_count", "nudge_count", "directive_level"]
    col_labels = ["Scenario", "Cond", "# Hyp", "Type Div",
                  "Score Gap", "Empathy", "Nudge", "Directive"]

    table_data = []
    for m in sorted(metrics, key=lambda x: (x["scenario_id"], x["condition"])):
        row = []
        for c in cols:
            val = m.get(c, "")
            row.append(str(val) if val is not None else "-")
        table_data.append(row)

    fig, ax = plt.subplots(figsize=(12, max(3, len(table_data) * 0.4 + 1)))
    ax.axis("off")
    table = ax.table(cellText=table_data, colLabels=col_labels,
                     cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.4)

    # Header styling
    for j in range(len(col_labels)):
        table[0, j].set_facecolor("#4C72B0")
        table[0, j].set_text_props(color="white", weight="bold")

    fig.suptitle("Fig. D: Per-Run Summary", fontsize=13, y=0.98)

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "fig_d_summary_table.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved fig_d_summary_table.png")


def generate_all():
    """Generate all figures."""
    metrics = load_metrics()
    logger.info(f"Loaded {len(metrics)} runs from {METRICS_CSV}")

    fig_a_judge_scores(metrics)
    fig_b_type_diversity(metrics)
    fig_c_empathy_nudge(metrics)
    fig_d_summary_table(metrics)

    print(f"\nAll figures saved to {FIGURES_DIR}/")


def main():
    logging.basicConfig(level=logging.INFO)
    generate_all()


if __name__ == "__main__":
    main()
