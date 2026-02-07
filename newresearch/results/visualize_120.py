#!/usr/bin/env python3
"""
120-run experiment visualization (3 Personas × 10 Scenarios × 4 Conditions)
Generates 8 figures for journal paper.
"""

import json, os, glob, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

plt.rcParams["font.family"] = "DejaVu Sans"
plt.rcParams["font.size"] = 11

BASE = "/home/c0a22080fa/AI-one-hour/newresearch/results/runs"
OUT  = "/home/c0a22080fa/AI-one-hour/newresearch/results/figures_120"
os.makedirs(OUT, exist_ok=True)

# ── Constants ──
CONDITIONS = ["A", "B", "C", "D"]
COND_LABELS = {
    "A": "A (Full)",
    "B": "B (−PKG)",
    "C": "C (−RAG)",
    "D": "D (Single/CoT)",
}
PERSONAS = ["P01", "P05", "P07"]
PERSONA_NAMES = {"P01": "Sugiura(47M)", "P05": "Suzuki(53M)", "P07": "Okada(27F)"}
SCENARIOS = [f"S{i}" for i in range(1, 11)]
SCENARIO_SHORT = {
    "S1": "S1:Authenticity", "S2": "S2:Efficiency", "S3": "S3:Tradition",
    "S4": "S4:Local-food", "S5": "S5:Budget", "S6": "S6:Nature-exp",
    "S7": "S7:Safety", "S8": "S8:Nostalgia", "S9": "S9:Cost-trap",
    "S10": "S10:SNS-record",
}
COND_COLORS = {"A": "#2196F3", "B": "#FF9800", "C": "#4CAF50", "D": "#9C27B0"}

# ── Data loading ──
def find_run_dir(cond, persona, scenario):
    """Find the latest run directory matching __Pxx__Sx__ pattern."""
    pattern = os.path.join(BASE, cond, f"*__{persona}__{scenario}__*")
    dirs = sorted(glob.glob(pattern))
    if not dirs:
        return None
    return dirs[-1]  # latest

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def load_entry(run_dir):
    """Load all metrics from a single run directory."""
    entry = {}
    # decision
    dp = os.path.join(run_dir, "decision.json")
    if os.path.exists(dp):
        dec = load_json(dp)
        entry["selected"] = dec.get("selected_hypothesis_id", "")
        entry["contrasting"] = dec.get("contrasting_hypothesis_id", "")
        entry["rationale"] = dec.get("selection_rationale", "")
    # hypotheses
    hp = os.path.join(run_dir, "hypotheses.json")
    if os.path.exists(hp):
        hyps = load_json(hp)
        entry["hypotheses"] = hyps.get("hypotheses", [])
        entry["reframing_selected"] = False
        entry["hyp_count"] = len(entry["hypotheses"])
        entry["reframing_count"] = sum(1 for h in entry["hypotheses"] if h.get("is_reframing", False))
        for h in entry["hypotheses"]:
            if h.get("hypothesis_id") == entry.get("selected"):
                entry["selected_type"] = h.get("type", "unknown")
                entry["is_reframing"] = h.get("is_reframing", False)
                entry["reframing_selected"] = h.get("is_reframing", False)
    # evidence
    ep = os.path.join(run_dir, "evidence.json")
    if os.path.exists(ep):
        ev = load_json(ep)
        entry["oext_count"] = len(ev.get("external_observations", []))
        entry["rag_count"] = len(ev.get("evidence_items", []))
    else:
        entry["oext_count"] = 0
        entry["rag_count"] = 0
    # judgements
    jp = os.path.join(run_dir, "judgements.json")
    if os.path.exists(jp):
        jd = load_json(jp)
        judgements = jd.get("judgements", [])
        sel_id = entry.get("selected", "")
        entry["selected_fatal"] = 0
        entry["total_fatal"] = 0
        for j in judgements:
            flaws = j.get("diagnosis", {}).get("fatal_flaws", [])
            real_flaws = [f for f in (flaws or []) if f and f != "(none)"]
            entry["total_fatal"] += len(real_flaws)
            if j.get("hypothesis_id") == sel_id:
                entry["selected_fatal"] = len(real_flaws)
        for j in judgements:
            if j.get("hypothesis_id") == sel_id:
                ec = j.get("diagnosis", {}).get("explains_confirmed", [])
                entry["explains_confirmed"] = len(ec) if ec else 0
    else:
        entry["explains_confirmed"] = 0
    # context
    cp = os.path.join(run_dir, "context.json")
    if os.path.exists(cp):
        ctx = load_json(cp)
        entry["obs_count"] = len(ctx.get("observations", []))
        entry["assumption_count"] = len(ctx.get("assumptions", []))
    return entry

# ── Collect all 120 runs ──
data = {}  # key = (condition, persona, scenario)
missing = []
for c in CONDITIONS:
    for p in PERSONAS:
        for s in SCENARIOS:
            d = find_run_dir(c, p, s)
            if not d:
                missing.append(f"{c}/{p}/{s}")
                continue
            data[(c, p, s)] = load_entry(d)

print(f"Loaded {len(data)} / 120 runs")
if missing:
    print(f"Missing: {missing}")

# ── Helper: aggregate by condition ──
def by_condition(metric, default=0):
    """Return {cond: [values across all P×S]}"""
    result = {}
    for c in CONDITIONS:
        vals = []
        for p in PERSONAS:
            for s in SCENARIOS:
                e = data.get((c, p, s), {})
                vals.append(e.get(metric, default))
        result[c] = vals
    return result

def reframing_rate_by_condition():
    """Return {cond: rate%}"""
    result = {}
    for c in CONDITIONS:
        cnt = sum(1 for p in PERSONAS for s in SCENARIOS
                  if data.get((c, p, s), {}).get("reframing_selected", False))
        result[c] = cnt / 30 * 100
    return result


# ═══════════════════════════════════════════════════════════════
# Figure 1: Reframing Rate by Condition (Bar Chart — headline)
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
rates = reframing_rate_by_condition()
bars = ax.bar(CONDITIONS, [rates[c] for c in CONDITIONS],
              color=[COND_COLORS[c] for c in CONDITIONS],
              alpha=0.88, edgecolor="white", linewidth=2)
for bar, c in zip(bars, CONDITIONS):
    cnt = sum(1 for p in PERSONAS for s in SCENARIOS
              if data.get((c, p, s), {}).get("reframing_selected", False))
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
            f"{cnt}/30\n({rates[c]:.1f}%)",
            ha="center", va="bottom", fontsize=12, fontweight="bold")

ax.set_xticks(range(len(CONDITIONS)))
ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=11)
ax.set_ylabel("Reframing Rate (%)", fontsize=12)
ax.set_title("Fig 1: Reframing Selection Rate by Condition  (N=30 per condition)",
             fontsize=13, fontweight="bold")
ax.set_ylim(0, 110)
ax.axhline(y=50, color="gray", linestyle="--", alpha=0.4)
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig1_reframing_rate.png"), dpi=200, bbox_inches="tight")
print("Saved fig1")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Figure 2: Reframing Heatmap (Persona × Scenario) per Condition
# ═══════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 4, figsize=(20, 5), sharey=True)
colors_rf = np.array([[0.92, 0.92, 0.92, 1.0],   # 0 = not reframing
                       [0.20, 0.60, 0.86, 1.0]])    # 1 = reframing

for ci, c in enumerate(CONDITIONS):
    ax = axes[ci]
    matrix = np.zeros((len(PERSONAS), len(SCENARIOS)))
    for pi, p in enumerate(PERSONAS):
        for si, s in enumerate(SCENARIOS):
            e = data.get((c, p, s), {})
            matrix[pi, si] = 1 if e.get("reframing_selected", False) else 0
    # draw
    img = np.zeros((*matrix.shape, 4))
    for i in range(len(PERSONAS)):
        for j in range(len(SCENARIOS)):
            img[i, j] = colors_rf[int(matrix[i, j])]
    ax.imshow(img, aspect="auto")
    # annotations
    for pi, p in enumerate(PERSONAS):
        for si, s in enumerate(SCENARIOS):
            e = data.get((c, p, s), {})
            sel = e.get("selected", "?")
            is_r = e.get("reframing_selected", False)
            label = sel + (" ★" if is_r else "")
            color = "white" if is_r else "black"
            ax.text(si, pi, label, ha="center", va="center",
                    fontsize=7, fontweight="bold", color=color)
    ax.set_xticks(range(len(SCENARIOS)))
    ax.set_xticklabels([f"S{i+1}" for i in range(10)], fontsize=8, rotation=45)
    if ci == 0:
        ax.set_yticks(range(len(PERSONAS)))
        ax.set_yticklabels([PERSONA_NAMES[p] for p in PERSONAS], fontsize=9)
    rate = sum(matrix.flatten()) / (len(PERSONAS) * len(SCENARIOS)) * 100
    ax.set_title(f"{COND_LABELS[c]}\n({rate:.0f}%)", fontsize=11, fontweight="bold")

p1 = mpatches.Patch(color=colors_rf[1], label="REFRAMING selected")
p2 = mpatches.Patch(color=colors_rf[0], label="Non-REFRAMING")
fig.legend(handles=[p1, p2], loc="lower center", ncol=2, fontsize=10,
           bbox_to_anchor=(0.5, -0.02))
fig.suptitle("Fig 2: Reframing Selection Heatmap  (★ = Reframing)  [3P × 10S × 4C]",
             fontsize=14, fontweight="bold")
fig.tight_layout(rect=[0, 0.03, 1, 0.93])
fig.savefig(os.path.join(OUT, "fig2_reframing_heatmap.png"), dpi=200, bbox_inches="tight")
print("Saved fig2")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Figure 3: Reframing Rate by Persona × Condition (Grouped Bar)
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 5))
x = np.arange(len(PERSONAS))
width = 0.18

for ci, c in enumerate(CONDITIONS):
    vals = []
    for p in PERSONAS:
        cnt = sum(1 for s in SCENARIOS
                  if data.get((c, p, s), {}).get("reframing_selected", False))
        vals.append(cnt / 10 * 100)
    bars = ax.bar(x + ci * width - 1.5 * width, vals, width,
                  label=COND_LABELS[c], color=COND_COLORS[c], alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"{v:.0f}%", ha="center", va="bottom", fontsize=9, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels([PERSONA_NAMES[p] for p in PERSONAS], fontsize=11)
ax.set_ylabel("Reframing Rate (%)", fontsize=12)
ax.set_title("Fig 3: Reframing Rate by Persona × Condition  (N=10 per cell)",
             fontsize=13, fontweight="bold")
ax.legend(fontsize=9)
ax.set_ylim(0, 115)
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig3_reframing_by_persona.png"), dpi=200, bbox_inches="tight")
print("Saved fig3")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Figure 4: Oext (External Observations) Distribution by Condition
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
oext = by_condition("oext_count", 0)

positions = range(len(CONDITIONS))
bp = ax.boxplot([oext[c] for c in CONDITIONS], positions=positions, widths=0.5,
                patch_artist=True, showmeans=True,
                meanprops=dict(marker="D", markerfacecolor="red", markersize=6))
for patch, c in zip(bp["boxes"], CONDITIONS):
    patch.set_facecolor(COND_COLORS[c])
    patch.set_alpha(0.6)

# add individual points (jittered)
for ci, c in enumerate(CONDITIONS):
    y = oext[c]
    jitter = np.random.normal(0, 0.06, len(y))
    ax.scatter([ci + 1 + j for j in jitter], y, alpha=0.4, s=15, c=COND_COLORS[c], zorder=5)

ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=11)
ax.set_ylabel("Oext Count (External Observations)", fontsize=12)
ax.set_title("Fig 4: External Observations per Run by Condition",
             fontsize=13, fontweight="bold")
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig4_oext_boxplot.png"), dpi=200, bbox_inches="tight")
print("Saved fig4")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Figure 5: Groundedness (explains_confirmed) Distribution
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
ec_data = by_condition("explains_confirmed", 0)

bp = ax.boxplot([ec_data[c] for c in CONDITIONS], positions=range(len(CONDITIONS)),
                widths=0.5, patch_artist=True, showmeans=True,
                meanprops=dict(marker="D", markerfacecolor="red", markersize=6))
for patch, c in zip(bp["boxes"], CONDITIONS):
    patch.set_facecolor(COND_COLORS[c])
    patch.set_alpha(0.6)

for ci, c in enumerate(CONDITIONS):
    y = ec_data[c]
    jitter = np.random.normal(0, 0.06, len(y))
    ax.scatter([ci + 1 + j for j in jitter], y, alpha=0.4, s=15, c=COND_COLORS[c], zorder=5)

ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=11)
ax.set_ylabel("Observations Explained (explains_confirmed)", fontsize=12)
ax.set_title("Fig 5: Groundedness by Condition",
             fontsize=13, fontweight="bold")
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig5_groundedness_boxplot.png"), dpi=200, bbox_inches="tight")
print("Saved fig5")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Figure 6: Selected Hypothesis Type Distribution (Stacked Bar)
# ═══════════════════════════════════════════════════════════════
type_colors = {
    "psychological": "#E91E63",
    "environmental": "#4CAF50",
    "goal_mismatch": "#FF9800",
    "evidence_gap": "#607D8B",
    "value": "#2196F3",
    "social": "#9C27B0",
    "skill": "#795548",
    "constraint_conflict": "#00BCD4",
    "unknown": "#BDBDBD",
}

fig, ax = plt.subplots(figsize=(8, 5))
type_counts = {}
all_types = set()
for c in CONDITIONS:
    type_counts[c] = {}
    for p in PERSONAS:
        for s in SCENARIOS:
            e = data.get((c, p, s), {})
            t = e.get("selected_type", "unknown")
            type_counts[c][t] = type_counts[c].get(t, 0) + 1
            all_types.add(t)

all_types = sorted(all_types)
x = np.arange(len(CONDITIONS))
bottom = np.zeros(len(CONDITIONS))

for t in all_types:
    vals = [type_counts[c].get(t, 0) for c in CONDITIONS]
    ax.bar(x, vals, bottom=bottom, label=t,
           color=type_colors.get(t, "#999"), alpha=0.85, edgecolor="white", linewidth=0.5)
    # annotate non-zero segments
    for i, v in enumerate(vals):
        if v > 0:
            ax.text(i, bottom[i] + v / 2, str(v),
                    ha="center", va="center", fontsize=8, fontweight="bold", color="white")
    bottom += vals

ax.set_xticks(x)
ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=11)
ax.set_ylabel("Count (N=30 per condition)", fontsize=12)
ax.set_title("Fig 6: Selected Hypothesis Type Distribution",
             fontsize=13, fontweight="bold")
ax.legend(fontsize=8, loc="upper right", ncol=2)
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig6_hypothesis_types.png"), dpi=200, bbox_inches="tight")
print("Saved fig6")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Figure 7: Fatal Flaws Distribution
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(7, 5))
fatal_data = by_condition("selected_fatal", 0)

bp = ax.boxplot([fatal_data[c] for c in CONDITIONS], positions=range(len(CONDITIONS)),
                widths=0.5, patch_artist=True, showmeans=True,
                meanprops=dict(marker="D", markerfacecolor="red", markersize=6))
for patch, c in zip(bp["boxes"], CONDITIONS):
    patch.set_facecolor(COND_COLORS[c])
    patch.set_alpha(0.6)

for ci, c in enumerate(CONDITIONS):
    y = fatal_data[c]
    jitter = np.random.normal(0, 0.06, len(y))
    ax.scatter([ci + 1 + j for j in jitter], y, alpha=0.4, s=15, c=COND_COLORS[c], zorder=5)

ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=11)
ax.set_ylabel("Fatal Flaws in Selected Hypothesis", fontsize=12)
ax.set_title("Fig 7: Quality Gate — Fatal Flaws by Condition",
             fontsize=13, fontweight="bold")
ax.grid(axis="y", alpha=0.2)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig7_fatal_flaws.png"), dpi=200, bbox_inches="tight")
print("Saved fig7")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Figure 8: Reframing vs Groundedness Scatter
# ═══════════════════════════════════════════════════════════════
fig, ax = plt.subplots(figsize=(8, 6))
marker_shapes = {"A": "o", "B": "s", "C": "^", "D": "D"}

for c in CONDITIONS:
    rf_vals, nrf_vals = [], []
    for p in PERSONAS:
        for s in SCENARIOS:
            e = data.get((c, p, s), {})
            oext = e.get("oext_count", 0)
            ec = e.get("explains_confirmed", 0)
            is_r = e.get("reframing_selected", False)
            if is_r:
                rf_vals.append((oext, ec))
            else:
                nrf_vals.append((oext, ec))

    if nrf_vals:
        xs, ys = zip(*nrf_vals)
        ax.scatter(xs, ys, s=50, marker=marker_shapes[c],
                   c=COND_COLORS[c], edgecolors="gray", linewidths=0.5,
                   alpha=0.5, zorder=3)
    if rf_vals:
        xs, ys = zip(*rf_vals)
        ax.scatter(xs, ys, s=120, marker=marker_shapes[c],
                   c=COND_COLORS[c], edgecolors="gold", linewidths=2,
                   alpha=0.9, zorder=5)

# legend
cond_handles = [plt.Line2D([0],[0], marker=marker_shapes[c], color="w",
                markerfacecolor=COND_COLORS[c], markersize=8,
                label=COND_LABELS[c]) for c in CONDITIONS]
rf_handle = plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="gray",
                        markeredgecolor="gold", markeredgewidth=2, markersize=10,
                        label="REFRAMING ★")
nrf_handle = plt.Line2D([0],[0], marker="o", color="w", markerfacecolor="gray",
                         markeredgecolor="gray", markeredgewidth=0.5, markersize=8,
                         label="Non-REFRAMING")
ax.legend(handles=cond_handles + [rf_handle, nrf_handle], fontsize=9, loc="upper left")
ax.set_xlabel("Oext Count (External Evidence)", fontsize=12)
ax.set_ylabel("Observations Explained", fontsize=12)
ax.set_title("Fig 8: Reframing vs Groundedness  (N=120)",
             fontsize=13, fontweight="bold")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fig8_scatter.png"), dpi=200, bbox_inches="tight")
print("Saved fig8")
plt.close(fig)


# ═══════════════════════════════════════════════════════════════
# Print summary stats for verification
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SUMMARY STATISTICS")
print("=" * 60)
rates = reframing_rate_by_condition()
for c in CONDITIONS:
    cnt = sum(1 for p in PERSONAS for s in SCENARIOS
              if data.get((c, p, s), {}).get("reframing_selected", False))
    oext_vals = [data.get((c, p, s), {}).get("oext_count", 0)
                 for p in PERSONAS for s in SCENARIOS]
    ec_vals = [data.get((c, p, s), {}).get("explains_confirmed", 0)
               for p in PERSONAS for s in SCENARIOS]
    fatal_vals = [data.get((c, p, s), {}).get("selected_fatal", 0)
                  for p in PERSONAS for s in SCENARIOS]
    print(f"\n{COND_LABELS[c]}:")
    print(f"  Reframing: {cnt}/30 ({rates[c]:.1f}%)")
    print(f"  Oext:   mean={np.mean(oext_vals):.2f}, median={np.median(oext_vals):.1f}")
    print(f"  Expl:   mean={np.mean(ec_vals):.2f}, median={np.median(ec_vals):.1f}")
    print(f"  Fatal:  mean={np.mean(fatal_vals):.2f}, total={sum(fatal_vals)}")

# Per persona
print("\n" + "-" * 40)
print("Reframing by Persona × Condition:")
for p in PERSONAS:
    line = f"  {PERSONA_NAMES[p]}: "
    for c in CONDITIONS:
        cnt = sum(1 for s in SCENARIOS
                  if data.get((c, p, s), {}).get("reframing_selected", False))
        line += f"{c}={cnt}/10  "
    print(line)

print(f"\nAll figures saved to {OUT}/")
