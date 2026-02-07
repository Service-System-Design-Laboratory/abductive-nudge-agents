"""
ABCD Condition Comparison Report — generates a single multi-panel PNG
from metrics.csv (S1 results).

Usage:
    python -m newresearch.visualize_comparison
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np


METRICS_CSV = Path(__file__).parent / "results" / "metrics.csv"
FIGURES_DIR = Path(__file__).parent / "results" / "figures"

# ── Condition metadata ──────────────────────────────────────────────
COND_ORDER = ["A", "B", "C", "D"]
COND_LABELS = {
    "A": "A (Full)",
    "B": "B (−PKG)",
    "C": "C (−RAG)",
    "D": "D (−Judge)",
}
COND_COLORS = {
    "A": "#4C72B0",
    "B": "#DD8452",
    "C": "#55A868",
    "D": "#C44E52",
}
ABLATION_DESC = {
    "A": "PKG:ON  RAG:ON  Judge:ON",
    "B": "PKG:OFF RAG:ON  Judge:ON",
    "C": "PKG:ON  RAG:OFF Judge:ON",
    "D": "PKG:ON  RAG:ON  Judge:OFF",
}


# ── Japanese font ───────────────────────────────────────────────────
def _setup_font():
    jp_fonts = []
    for f in fm.findSystemFonts():
        fname = f.lower()
        if any(k in fname for k in [
            "notosanscjk", "notosansjp", "ipag", "ipam",
            "ipagothic", "ipamincho",
        ]):
            jp_fonts.append(f)
    if jp_fonts:
        plt.rcParams["font.family"] = fm.FontProperties(fname=jp_fonts[0]).get_name()
    else:
        plt.rcParams["font.family"] = "DejaVu Sans"


def _load() -> dict[str, dict]:
    """Load metrics keyed by condition letter."""
    with open(METRICS_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {r["condition"]: r for r in rows}


def _val(row: dict, key: str, default=0) -> float:
    """Parse a metric value, returning default for empty/None."""
    v = row.get(key)
    if v is None or v == "" or v == "None":
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


# ── Figure generators ───────────────────────────────────────────────

def _ax_bar(ax, data: dict, metric_keys: list[str], metric_labels: list[str],
            title: str, ylabel: str = "Value", ylim_max: float | None = None,
            show_values: bool = True):
    """Generic grouped-bar plotter."""
    conds = [c for c in COND_ORDER if c in data]
    x = np.arange(len(metric_keys))
    width = 0.8 / len(conds)
    offsets = np.linspace(-0.4 + width / 2, 0.4 - width / 2, len(conds))

    for i, cond in enumerate(conds):
        vals = [_val(data[cond], k) for k in metric_keys]
        bars = ax.bar(x + offsets[i], vals, width * 0.9,
                      label=COND_LABELS.get(cond, cond),
                      color=COND_COLORS.get(cond, "#999"),
                      edgecolor="white", linewidth=0.5)
        if show_values:
            for bar, v in zip(bars, vals):
                if v > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
                            f"{v:.0f}" if v == int(v) else f"{v:.2f}",
                            ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, fontsize=8)
    ax.set_ylabel(ylabel, fontsize=9)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.legend(fontsize=7, loc="upper right")
    if ylim_max:
        ax.set_ylim(0, ylim_max)
    ax.grid(axis="y", alpha=0.25)


def generate_report():
    _setup_font()
    data = _load()
    conds = [c for c in COND_ORDER if c in data]

    fig = plt.figure(figsize=(18, 22))
    fig.suptitle("ABCD Ablation Comparison Report — S1",
                 fontsize=16, fontweight="bold", y=0.98)

    # ── Layout: 3×2 panels + 1 table row ───────────────────────────
    gs = fig.add_gridspec(4, 2, hspace=0.38, wspace=0.30,
                          top=0.94, bottom=0.03, left=0.07, right=0.95)

    # ────────────────────────────────────────────────────────────────
    # Panel 0: Summary table (top row, full width)
    # ────────────────────────────────────────────────────────────────
    ax_tbl = fig.add_subplot(gs[0, :])
    ax_tbl.axis("off")

    col_keys = [
        "condition", "observation_count", "external_observation_count",
        "hypothesis_count", "type_diversity",
        "persona_link_count", "evidence_link_count",
        "east_count", "empathy_count", "nudge_count",
        "response_length",
    ]
    col_labels = [
        "Condition", "Obs", "Oext", "# Hyp", "Type Div",
        "PKG Links", "Ev Links",
        "EAST", "Empathy", "Nudge",
        "Resp Len",
    ]
    table_data = []
    for c in conds:
        row = data[c]
        table_data.append([
            f"{c} ({ABLATION_DESC[c]})",
            *[str(int(_val(row, k))) if _val(row, k) == int(_val(row, k))
              else f"{_val(row, k):.2f}" for k in col_keys[1:]],
        ])

    tbl = ax_tbl.table(cellText=table_data, colLabels=col_labels,
                       cellLoc="center", loc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.6)
    # Header style
    for j in range(len(col_labels)):
        tbl[0, j].set_facecolor("#3b5998")
        tbl[0, j].set_text_props(color="white", weight="bold", fontsize=8)
    # Row colours
    row_colors = ["#f0f4ff", "#fff5ed", "#edfaef", "#fdedef"]
    for i in range(len(conds)):
        for j in range(len(col_labels)):
            tbl[i + 1, j].set_facecolor(row_colors[i])

    ax_tbl.set_title("Summary Table", fontsize=11, fontweight="bold", pad=12)

    # ────────────────────────────────────────────────────────────────
    # Panel 1: Information source links (PKG vs Evidence)
    # ────────────────────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[1, 0])
    _ax_bar(ax1, data,
            ["persona_link_count", "persona_link_unique",
             "evidence_link_count", "evidence_link_unique"],
            ["PKG Links\n(total)", "PKG Links\n(unique)",
             "Ev Links\n(total)", "Ev Links\n(unique)"],
            "① Information Source Links",
            ylabel="Count", ylim_max=14)

    # ────────────────────────────────────────────────────────────────
    # Panel 2: Hypothesis quality
    # ────────────────────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[1, 1])
    _ax_bar(ax2, data,
            ["hypothesis_count", "type_diversity",
             "observation_coverage", "avg_predictions_per_h", "avg_disc_questions_per_h"],
            ["# Hyp", "Type\nDiversity",
             "Obs\nCoverage", "Avg Pred\n/ Hyp", "Avg DiscQ\n/ Hyp"],
            "② Hypothesis Quality",
            ylabel="Value", ylim_max=7)

    # ────────────────────────────────────────────────────────────────
    # Panel 3: Judge diagnostic (A, B, C only — D has no Judge)
    # ────────────────────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[2, 0])
    judge_data = {c: data[c] for c in conds if _val(data[c], "fatal_flaw_avoided", -1) >= 0}
    if judge_data:
        _ax_bar(ax3, judge_data,
                ["fatal_flaw_avoided", "selected_is_max_explains",
                 "discriminating_q_coverage", "has_contrasting", "contrast_type_diff"],
                ["Fatal Flaw\nAvoided", "Max Explains\nSelected",
                 "Discrim Q\nCoverage", "Has\nContrast", "Contrast\nType Diff"],
                "③ Judge Diagnostic (D excluded — no Judge)",
                ylabel="Rate (0–1)", ylim_max=1.5)
    else:
        ax3.text(0.5, 0.5, "No Judge data available",
                 ha="center", va="center", fontsize=12, color="grey")
        ax3.set_title("③ Judge Diagnostic", fontsize=10, fontweight="bold")

    # ────────────────────────────────────────────────────────────────
    # Panel 4: EAST nudge markers
    # ────────────────────────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[2, 1])
    _ax_bar(ax4, data,
            ["east_easy", "east_attractive", "east_social", "east_timely", "east_count"],
            ["Easy", "Attractive", "Social", "Timely", "EAST\nCount"],
            "④ EAST Nudge Markers",
            ylabel="Value", ylim_max=5.5)

    # ────────────────────────────────────────────────────────────────
    # Panel 5: Empathy markers
    # ────────────────────────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[3, 0])
    _ax_bar(ax5, data,
            ["empathy_acknowledgement", "empathy_reflection",
             "empathy_perspective_prompt", "empathy_count"],
            ["Acknowledge", "Reflection",
             "Perspective\nPrompt", "Empathy\nCount"],
            "⑤ Empathy Markers",
            ylabel="Value", ylim_max=4.5)

    # ────────────────────────────────────────────────────────────────
    # Panel 6: Operational nudge sub-markers + response length
    # ────────────────────────────────────────────────────────────────
    ax6 = fig.add_subplot(gs[3, 1])
    # Normalise response_length for visual comparison
    _ax_bar(ax6, data,
            ["nudge_has_question", "nudge_has_options",
             "nudge_has_small_action", "nudge_count"],
            ["Has\nQuestion", "Has\nOptions",
             "Has Small\nAction", "Nudge\nCount"],
            "⑥ Nudge Sub-markers",
            ylabel="Value", ylim_max=4.5)

    # ── Save ────────────────────────────────────────────────────────
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = FIGURES_DIR / "abcd_comparison_report.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"✅  Report saved → {out_path}")

    # Also generate a compact text summary
    _text_summary(data, conds)


def _text_summary(data: dict, conds: list[str]):
    """Print a compact text comparison highlighting ablation effects."""
    lines = [
        "=" * 70,
        "ABCD ABLATION COMPARISON — KEY FINDINGS (S1)",
        "=" * 70,
        "",
    ]

    # PKG effect (A vs B)
    a, b = data.get("A", {}), data.get("B", {})
    lines += [
        "【PKG の効果】A (Full) vs B (−PKG)",
        f"  PKG Links:  A={_val(a, 'persona_link_count'):.0f}  vs  B={_val(b, 'persona_link_count'):.0f}",
        f"  Ev Links:   A={_val(a, 'evidence_link_count'):.0f}  vs  B={_val(b, 'evidence_link_count'):.0f}",
        f"  PKG unique: A={_val(a, 'persona_link_unique'):.0f}  vs  B={_val(b, 'persona_link_unique'):.0f}",
        f"  → PKG があると仮説が個人化される (persona_link ↑)",
        "",
    ]

    # RAG effect (A vs C)
    c = data.get("C", {})
    lines += [
        "【RAG の効果】A (Full) vs C (−RAG)",
        f"  Oext:       A={_val(a, 'external_observation_count'):.0f}  vs  C={_val(c, 'external_observation_count'):.0f}",
        f"  Ev Links:   A={_val(a, 'evidence_link_count'):.0f}  vs  C={_val(c, 'evidence_link_count'):.0f}",
        f"  Obs count:  A={_val(a, 'observation_count'):.0f}  vs  C={_val(c, 'observation_count'):.0f}",
        f"  → RAG がないと外部根拠が得られない (Oext=0, ev_link=0)",
        "",
    ]

    # Judge effect (A vs D)
    d = data.get("D", {})
    lines += [
        "【Judge の効果】A (Full) vs D (−Judge)",
        f"  Fatal OK:   A={_val(a, 'fatal_flaw_avoided'):.0f}  vs  D=N/A",
        f"  Contrast:   A={_val(a, 'has_contrasting'):.0f}  vs  D=N/A",
        f"  Resp Len:   A={_val(a, 'response_length'):.0f}  vs  D={_val(d, 'response_length'):.0f}",
        f"  → Judge がないと仮説の品質チェックが省略される",
        "",
    ]

    # EAST
    lines += [
        "【EAST ナッジ】",
    ]
    for c_key in conds:
        r = data[c_key]
        east = f"E={_val(r, 'east_easy'):.0f} A={_val(r, 'east_attractive'):.0f} S={_val(r, 'east_social'):.0f} T={_val(r, 'east_timely'):.0f}"
        lines.append(f"  {c_key}: {east}  (count={_val(r, 'east_count'):.0f})")
    lines += ["", "=" * 70]

    summary = "\n".join(lines)
    print(summary)

    out_path = FIGURES_DIR / "abcd_comparison_summary.txt"
    out_path.write_text(summary, encoding="utf-8")
    print(f"✅  Text summary saved → {out_path}")


if __name__ == "__main__":
    generate_report()
