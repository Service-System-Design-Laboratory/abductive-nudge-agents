#!/usr/bin/env python3
"""v4実験結果の可視化 — 論文用図表の生成"""

import json, os, glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 11

BASE = "/home/c0a22080fa/AI-one-hour/newresearch/results/runs"
OUT  = "/home/c0a22080fa/AI-one-hour/newresearch/results/figures"
os.makedirs(OUT, exist_ok=True)

CONDITIONS = ["A", "B", "C", "D"]
COND_LABELS = {
    "A": "A (Full)",
    "B": "B (−PKG)",
    "C": "C (−RAG)",
    "D": "D (Single)",
}
SCENARIOS = ["S1", "S2", "S3"]
SCENARIO_LABELS = {
    "S1": "S1: Authenticity",
    "S2": "S2: Efficiency",
    "S3": "S3: Tradition",
}

def find_run_dir(cond, scenario):
    pattern = os.path.join(BASE, cond, f"*__{scenario}__*")
    dirs = sorted(glob.glob(pattern))
    return dirs[-1] if dirs else None  # latest (v4) run

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

# ── Collect data ──
data = {}
for c in CONDITIONS:
    for s in SCENARIOS:
        d = find_run_dir(c, s)
        if not d:
            continue
        key = (c, s)
        entry = {}
        # decision
        dp = os.path.join(d, "decision.json")
        if os.path.exists(dp):
            dec = load_json(dp)
            entry["selected"] = dec.get("selected_hypothesis_id", "")
            entry["contrasting"] = dec.get("contrasting_hypothesis_id", "")
            entry["rationale"] = dec.get("selection_rationale", "")
        # hypotheses
        hp = os.path.join(d, "hypotheses.json")
        if os.path.exists(hp):
            hyps = load_json(hp)
            entry["hypotheses"] = hyps.get("hypotheses", [])
            entry["reframing_selected"] = False
            for h in entry["hypotheses"]:
                if h.get("hypothesis_id") == entry.get("selected"):
                    entry["selected_type"] = h.get("type", "")
                    entry["is_reframing"] = h.get("is_reframing", False)
                    entry["reframing_selected"] = h.get("is_reframing", False)
                    entry["selected_statement"] = h.get("statement", "")[:60]
        # evidence
        ep = os.path.join(d, "evidence.json")
        if os.path.exists(ep):
            ev = load_json(ep)
            entry["oext_count"] = len(ev.get("external_observations", []))
            entry["rag_count"] = len(ev.get("evidence_items", []))
            entry["oext_texts"] = [o.get("text","")[:40] for o in ev.get("external_observations",[])]
        else:
            entry["oext_count"] = 0
            entry["rag_count"] = 0
        # judgements
        jp = os.path.join(d, "judgements.json")
        if os.path.exists(jp):
            jd = load_json(jp)
            judgements = jd.get("judgements", [])
            # count fatal flaws for selected hypothesis
            sel_id = entry.get("selected", "")
            entry["selected_fatal"] = 0
            entry["total_fatal"] = 0
            for j in judgements:
                flaws = j.get("diagnosis", {}).get("fatal_flaws", [])
                if flaws and flaws != ["(none)"] and flaws != [""]:
                    real_flaws = [f for f in flaws if f and f != "(none)"]
                    entry["total_fatal"] += len(real_flaws)
                    if j.get("hypothesis_id") == sel_id:
                        entry["selected_fatal"] = len(real_flaws)
            # count explains_confirmed for selected
            for j in judgements:
                if j.get("hypothesis_id") == sel_id:
                    ec = j.get("diagnosis", {}).get("explains_confirmed", [])
                    entry["explains_confirmed"] = len(ec) if ec else 0
                    entry["explains_list"] = ec if ec else []
        # context
        cp = os.path.join(d, "context.json")
        if os.path.exists(cp):
            ctx = load_json(cp)
            entry["obs_count"] = len(ctx.get("observations", []))
            entry["assumption_count"] = len(ctx.get("assumptions", []))
        data[key] = entry

print(f"Loaded {len(data)} runs")

# ═══════════════════════════════════════════════════
# Figure 1: Reframing Heatmap (S×C)
# ═══════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))
matrix = np.zeros((3, 4))
for si, s in enumerate(SCENARIOS):
    for ci, c in enumerate(CONDITIONS):
        e = data.get((c, s), {})
        matrix[si, ci] = 1 if e.get("reframing_selected", False) else 0

colors = np.array([[0.92, 0.92, 0.92, 1.0],   # 0 = not reframing (light gray)
                    [0.20, 0.60, 0.86, 1.0]])    # 1 = reframing (blue)
img = np.zeros((*matrix.shape, 4))
for i in range(3):
    for j in range(4):
        img[i, j] = colors[int(matrix[i, j])]
ax.imshow(img, aspect="auto")

for si, s in enumerate(SCENARIOS):
    for ci, c in enumerate(CONDITIONS):
        e = data.get((c, s), {})
        sel = e.get("selected", "?")
        is_r = e.get("reframing_selected", False)
        label = f"{sel}" + (" ★" if is_r else "")
        color = "white" if is_r else "black"
        ax.text(ci, si, label, ha="center", va="center", fontsize=14, fontweight="bold", color=color)

ax.set_xticks(range(4))
ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=11)
ax.set_yticks(range(3))
ax.set_yticklabels([SCENARIO_LABELS[s] for s in SCENARIOS], fontsize=11)
ax.set_title("Reframing Hypothesis Selection (★ = REFRAMING)", fontsize=13, fontweight="bold")

# legend
p1 = mpatches.Patch(color=colors[1], label="REFRAMING selected")
p2 = mpatches.Patch(color=colors[0], label="Non-REFRAMING selected")
ax.legend(handles=[p1, p2], loc="upper right", bbox_to_anchor=(1.0, -0.08), ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_reframing_heatmap.png"), dpi=200, bbox_inches="tight")
print("Saved fig1_reframing_heatmap.png")
plt.close(fig)

# ═══════════════════════════════════════════════════
# Figure 2: Oext Count by Condition
# ═══════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))
x = np.arange(len(SCENARIOS))
width = 0.18
cond_colors = {"A": "#2196F3", "B": "#FF9800", "C": "#4CAF50", "D": "#9C27B0"}

for ci, c in enumerate(CONDITIONS):
    vals = [data.get((c, s), {}).get("oext_count", 0) for s in SCENARIOS]
    bars = ax.bar(x + ci * width - 1.5 * width, vals, width, label=COND_LABELS[c], color=cond_colors[c], alpha=0.85)
    for bar, v in zip(bars, vals):
        if v > 0:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, str(v),
                    ha="center", va="bottom", fontsize=9, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIOS])
ax.set_ylabel("Number of Oext (External Observations)")
ax.set_title("External Observations (Oext) Generated per Condition", fontsize=13, fontweight="bold")
ax.legend(fontsize=9)
ax.set_ylim(0, 4.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig2_oext_count.png"), dpi=200, bbox_inches="tight")
print("Saved fig2_oext_count.png")
plt.close(fig)

# ═══════════════════════════════════════════════════
# Figure 3: Groundedness Radar — explains_confirmed count
# ═══════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))
for ci, c in enumerate(CONDITIONS):
    vals = []
    for s in SCENARIOS:
        e = data.get((c, s), {})
        vals.append(e.get("explains_confirmed", 0))
    bars = ax.bar(x + ci * width - 1.5 * width, vals, width, label=COND_LABELS[c], color=cond_colors[c], alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05, str(v),
                ha="center", va="bottom", fontsize=9, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIOS])
ax.set_ylabel("Observations Explained (explains_confirmed)")
ax.set_title("Groundedness: Observations Explained by Selected Hypothesis", fontsize=13, fontweight="bold")
ax.legend(fontsize=9)
ax.set_ylim(0, 8)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_groundedness.png"), dpi=200, bbox_inches="tight")
print("Saved fig3_groundedness.png")
plt.close(fig)

# ═══════════════════════════════════════════════════
# Figure 4: Selected Hypothesis Type Distribution
# ═══════════════════════════════════════════════════
type_counts = {}
for c in CONDITIONS:
    type_counts[c] = {}
    for s in SCENARIOS:
        e = data.get((c, s), {})
        t = e.get("selected_type", "unknown")
        type_counts[c][t] = type_counts[c].get(t, 0) + 1

all_types = sorted(set(t for tc in type_counts.values() for t in tc.keys()))
type_colors = {
    "psychological": "#E91E63",
    "environmental": "#4CAF50",
    "goal_mismatch": "#FF9800",
    "evidence_gap": "#607D8B",
    "value": "#2196F3",
    "social": "#9C27B0",
    "skill": "#795548",
    "constraint_conflict": "#00BCD4",
}

fig, axes = plt.subplots(1, 4, figsize=(14, 4))
for ci, c in enumerate(CONDITIONS):
    ax = axes[ci]
    tc = type_counts[c]
    labels = list(tc.keys())
    sizes = list(tc.values())
    cols = [type_colors.get(l, "#999999") for l in labels]
    wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct=lambda p: f"{int(round(p*sum(sizes)/100))}",
                                       colors=cols, startangle=90, textprops={"fontsize": 12, "fontweight": "bold"})
    ax.set_title(COND_LABELS[c], fontsize=12, fontweight="bold")

# shared legend
handles = [mpatches.Patch(color=type_colors.get(t, "#999"), label=t) for t in all_types]
fig.legend(handles=handles, loc="lower center", ncol=min(len(all_types), 5), fontsize=9, bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Selected Hypothesis Type Distribution", fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig4_hypothesis_types.png"), dpi=200, bbox_inches="tight")
print("Saved fig4_hypothesis_types.png")
plt.close(fig)

# ═══════════════════════════════════════════════════
# Figure 5: Comprehensive Dashboard — Reframing × Groundedness
# ═══════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
marker_shapes = {"A": "o", "B": "s", "C": "^", "D": "D"}

for c in CONDITIONS:
    for s in SCENARIOS:
        e = data.get((c, s), {})
        oext = e.get("oext_count", 0)
        ec = e.get("explains_confirmed", 0)
        is_r = e.get("reframing_selected", False)
        
        edge = "gold" if is_r else "gray"
        lw = 3 if is_r else 1
        ax.scatter(oext, ec, s=200, marker=marker_shapes[c], 
                   c=cond_colors[c], edgecolors=edge, linewidths=lw, zorder=5, alpha=0.9)
        offset_x = 0.08
        offset_y = 0.15
        ax.annotate(f"{s}", (oext + offset_x, ec + offset_y), fontsize=8, ha="left")

# legend for conditions
cond_handles = [plt.Line2D([0],[0], marker=marker_shapes[c], color="w", markerfacecolor=cond_colors[c],
                           markersize=10, label=COND_LABELS[c]) for c in CONDITIONS]
# legend for reframing
rf_handle = plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="gray",
                        markeredgecolor="gold", markeredgewidth=2, markersize=10, label="REFRAMING ★")
nrf_handle = plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="gray",
                         markeredgecolor="gray", markeredgewidth=1, markersize=10, label="Non-REFRAMING")

ax.legend(handles=cond_handles + [rf_handle, nrf_handle], fontsize=9, loc="upper left")
ax.set_xlabel("Oext Count (External Evidence)", fontsize=12)
ax.set_ylabel("Observations Explained (explains_confirmed)", fontsize=12)
ax.set_title("Reframing Occurrence vs Groundedness", fontsize=13, fontweight="bold")
ax.set_xlim(-0.5, 4)
ax.set_ylim(0, 8)
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig5_reframing_vs_groundedness.png"), dpi=200, bbox_inches="tight")
print("Saved fig5_reframing_vs_groundedness.png")
plt.close(fig)

# ═══════════════════════════════════════════════════
# Figure 6: Fatal Flaws in Selected Hypothesis
# ═══════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 4))
for ci, c in enumerate(CONDITIONS):
    vals = [data.get((c, s), {}).get("selected_fatal", 0) for s in SCENARIOS]
    bars = ax.bar(x + ci * width - 1.5 * width, vals, width, label=COND_LABELS[c], color=cond_colors[c], alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, str(v),
                ha="center", va="bottom", fontsize=9, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels([SCENARIO_LABELS[s] for s in SCENARIOS])
ax.set_ylabel("Fatal Flaws in Selected Hypothesis")
ax.set_title("Quality Gate: Fatal Flaws in Selected Hypothesis", fontsize=13, fontweight="bold")
ax.legend(fontsize=9)
ax.set_ylim(0, 2.5)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig6_fatal_flaws.png"), dpi=200, bbox_inches="tight")
print("Saved fig6_fatal_flaws.png")
plt.close(fig)

# ═══════════════════════════════════════════════════
# Figure 7: Summary Table (text-based)
# ═══════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(12, 5))
ax.axis("off")

col_labels = [COND_LABELS[c] for c in CONDITIONS]
row_labels = [SCENARIO_LABELS[s] for s in SCENARIOS]

cell_text = []
cell_colors = []
for s in SCENARIOS:
    row = []
    row_c = []
    for c in CONDITIONS:
        e = data.get((c, s), {})
        sel = e.get("selected", "?")
        is_r = e.get("reframing_selected", False)
        oext = e.get("oext_count", 0)
        ec = e.get("explains_confirmed", 0)
        fatal = e.get("selected_fatal", 0)
        star = " ★" if is_r else ""
        txt = f"{sel}{star}\nOext={oext}  Expl={ec}\nFlaws={fatal}"
        row.append(txt)
        if is_r and fatal == 0:
            row_c.append("#C8E6C9")  # green - good reframing
        elif is_r and fatal > 0:
            row_c.append("#FFF9C4")  # yellow - reframing with flaws
        else:
            row_c.append("#FFCDD2")  # red - no reframing
    cell_text.append(row)
    cell_colors.append(row_c)

table = ax.table(cellText=cell_text, rowLabels=row_labels, colLabels=col_labels,
                  cellColours=cell_colors, loc="center", cellLoc="center")
table.auto_set_font_size(False)
table.set_fontsize(10)
table.scale(1.0, 2.5)

# color header
for j in range(4):
    table[0, j].set_facecolor("#E3F2FD")
    table[0, j].set_text_props(fontweight="bold")
for i in range(3):
    table[i+1, -1].set_text_props(fontweight="bold")

ax.set_title("v4 Experiment Summary: Selected Hypothesis × Groundedness Metrics",
             fontsize=14, fontweight="bold", pad=20)

# legend
legend_text = "★ = REFRAMING | Green = Reframing (no flaws) | Yellow = Reframing (with flaws) | Red = No Reframing"
fig.text(0.5, 0.02, legend_text, ha="center", fontsize=9, style="italic")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig7_summary_table.png"), dpi=200, bbox_inches="tight")
print("Saved fig7_summary_table.png")
plt.close(fig)

# ═══════════════════════════════════════════════════
# Figure 8: Reframing Rate Bar Chart
# ═══════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(6, 4))
rates = []
for c in CONDITIONS:
    cnt = sum(1 for s in SCENARIOS if data.get((c, s), {}).get("reframing_selected", False))
    rates.append(cnt / 3 * 100)

bars = ax.bar(range(4), rates, color=[cond_colors[c] for c in CONDITIONS], alpha=0.85, edgecolor="white", linewidth=2)
for bar, r, c in zip(bars, rates, CONDITIONS):
    cnt = sum(1 for s in SCENARIOS if data.get((c, s), {}).get("reframing_selected", False))
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f"{cnt}/3\n({r:.0f}%)", ha="center", va="bottom", fontsize=11, fontweight="bold")

ax.set_xticks(range(4))
ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=11)
ax.set_ylabel("Reframing Rate (%)", fontsize=12)
ax.set_title("Reframing Hypothesis Selection Rate by Condition", fontsize=13, fontweight="bold")
ax.set_ylim(0, 120)
ax.axhline(y=50, color="gray", linestyle="--", alpha=0.4, label="50% baseline")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig8_reframing_rate.png"), dpi=200, bbox_inches="tight")
print("Saved fig8_reframing_rate.png")
plt.close(fig)

print(f"\nAll figures saved to {OUT}/")
