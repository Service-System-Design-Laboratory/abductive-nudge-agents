#!/usr/bin/env python3
"""
Fig 9: Why A(Full) has the lowest reframing rate —
       Fatal-flaw mechanism caused by persona_link hallucination.
"""
import json, os, glob
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

CONDITIONS = ["A", "B", "C", "D"]
COND_LABELS = {
    "A": "A (Full)", "B": "B (−PKG)", "C": "C (−RAG)", "D": "D (Single/CoT)",
}
COND_COLORS = {"A": "#2196F3", "B": "#FF9800", "C": "#4CAF50", "D": "#9C27B0"}

# ── Data collection ──
def collect_data():
    """Collect fatal_flaw and reframing stats per condition."""
    results = {}
    for cond in ["A", "B", "C"]:
        dirs = sorted(glob.glob(os.path.join(BASE, cond, "*__P0*__S*__*")))
        stats = {
            "total": 0,
            "reframe_available": 0,
            "reframe_selected": 0,
            "reframe_has_fatal": 0,
            "reframe_no_fatal": 0,
            "fatal_and_selected": 0,
            "fatal_and_not_selected": 0,
            "nofatal_and_selected": 0,
            "nofatal_and_not_selected": 0,
            "fatal_reasons": [],
        }
        for d in dirs:
            hp = os.path.join(d, "hypotheses.json")
            dp = os.path.join(d, "decision.json")
            jp = os.path.join(d, "judgements.json")
            if not os.path.exists(hp) or not os.path.exists(dp):
                continue
            with open(hp) as f: hyps = json.load(f)
            with open(dp) as f: dec = json.load(f)

            selected_id = dec.get("selected_hypothesis_id", "")
            hypotheses = hyps.get("hypotheses", [])
            reframing_hyps = [h for h in hypotheses if h.get("is_reframing")]

            stats["total"] += 1
            if reframing_hyps:
                stats["reframe_available"] += 1

            selected_is_reframing = any(
                h.get("hypothesis_id") == selected_id and h.get("is_reframing")
                for h in hypotheses
            )
            if selected_is_reframing:
                stats["reframe_selected"] += 1

            # Judge fatal flaw on reframing hyp
            reframing_has_fatal = False
            if os.path.exists(jp):
                with open(jp) as f: jd = json.load(f)
                judgements = jd.get("judgements", [])
                for rh in reframing_hyps:
                    for j in judgements:
                        if j.get("hypothesis_id") == rh.get("hypothesis_id"):
                            flaws = j.get("diagnosis", {}).get("fatal_flaws", [])
                            real_flaws = [fl for fl in (flaws or []) if fl and fl != "(none)"]
                            if real_flaws:
                                reframing_has_fatal = True
                                for fl in real_flaws:
                                    if "PKG" in fl or "persona_link" in fl:
                                        stats["fatal_reasons"].append("hallucinated_pkg_id")
                                    else:
                                        stats["fatal_reasons"].append("other")

            if reframing_has_fatal:
                stats["reframe_has_fatal"] += 1
                if selected_is_reframing:
                    stats["fatal_and_selected"] += 1
                else:
                    stats["fatal_and_not_selected"] += 1
            else:
                stats["reframe_no_fatal"] += 1
                if selected_is_reframing:
                    stats["nofatal_and_selected"] += 1
                else:
                    stats["nofatal_and_not_selected"] += 1

        results[cond] = stats
    return results

data = collect_data()

# ────────────────────────────────────────────────
# Fig 9a: Stacked bar — fatal_flaw rate on reframing hyp per condition
# ────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(16, 6), gridspec_kw={"width_ratios": [1.2, 1.2, 1.2]})

# Panel 1: Fatal flaw rate on reframing hypotheses
ax = axes[0]
conds_abc = ["A", "B", "C"]
fatal_rates = []
nofatal_rates = []
for c in conds_abc:
    s = data[c]
    total = s["reframe_has_fatal"] + s["reframe_no_fatal"]
    fatal_rates.append(s["reframe_has_fatal"] / total * 100 if total > 0 else 0)
    nofatal_rates.append(s["reframe_no_fatal"] / total * 100 if total > 0 else 0)

x = np.arange(len(conds_abc))
bars1 = ax.bar(x, fatal_rates, 0.5, color="#E53935", label="Fatal flaw (PKG hallucination)")
bars2 = ax.bar(x, nofatal_rates, 0.5, bottom=fatal_rates, color="#81C784", label="No fatal flaw")
ax.set_xticks(x)
ax.set_xticklabels([COND_LABELS[c] for c in conds_abc])
ax.set_ylabel("% of reframing hypotheses")
ax.set_title("(a) Fatal flaw rate on\nreframing hypotheses", fontweight="bold")
ax.set_ylim(0, 110)
ax.legend(loc="upper right", fontsize=9)
for i, (fr, nfr) in enumerate(zip(fatal_rates, nofatal_rates)):
    if fr > 0:
        ax.text(i, fr/2, f"{fr:.0f}%", ha="center", va="center", color="white", fontweight="bold")
    if nfr > 0:
        ax.text(i, fr + nfr/2, f"{nfr:.0f}%", ha="center", va="center", color="black", fontweight="bold")

# Panel 2: Reframing selection rate — split by fatal/no-fatal (A only)
ax = axes[1]
s = data["A"]
# 2×2 grouped bar
categories = ["Fatal flaw\non reframing", "No fatal flaw\non reframing"]
selected_vals = [
    s["fatal_and_selected"] / (s["fatal_and_selected"] + s["fatal_and_not_selected"]) * 100
    if (s["fatal_and_selected"] + s["fatal_and_not_selected"]) > 0 else 0,
    s["nofatal_and_selected"] / (s["nofatal_and_selected"] + s["nofatal_and_not_selected"]) * 100
    if (s["nofatal_and_selected"] + s["nofatal_and_not_selected"]) > 0 else 0,
]
n_vals = [
    s["fatal_and_selected"] + s["fatal_and_not_selected"],
    s["nofatal_and_selected"] + s["nofatal_and_not_selected"],
]

bars = ax.bar([0, 1], selected_vals, 0.5, color=["#E53935", "#81C784"])
ax.set_xticks([0, 1])
ax.set_xticklabels(categories, fontsize=10)
ax.set_ylabel("Reframing selection rate (%)")
ax.set_title("(b) A(Full): Reframing selection rate\nby fatal flaw status", fontweight="bold")
ax.set_ylim(0, 120)
for i, (v, n) in enumerate(zip(selected_vals, n_vals)):
    ax.text(i, v + 3, f"{v:.0f}%\n(n={n})", ha="center", va="bottom", fontweight="bold", fontsize=11)

# Panel 3: Causal flow diagram (text-based)
ax = axes[2]
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis("off")
ax.set_title("(c) Causal mechanism:\nPKG hallucination → suppression", fontweight="bold")

# Draw flow boxes
box_style = dict(boxstyle="round,pad=0.4", facecolor="#E3F2FD", edgecolor="#1565C0", linewidth=1.5)
box_red = dict(boxstyle="round,pad=0.4", facecolor="#FFEBEE", edgecolor="#C62828", linewidth=1.5)
box_green = dict(boxstyle="round,pad=0.4", facecolor="#E8F5E9", edgecolor="#2E7D32", linewidth=1.5)

# Flow: top to bottom
steps = [
    (5, 9.2, "HypothesisAgent generates\nreframing with persona_link\n[pkg:n7, pkg:n158...]", box_style),
    (5, 7.2, "LLM hallucinated node IDs\n(not in Neo4j PKG graph)", box_red),
    (5, 5.2, "JudgeAgent: verify_persona_links()\n→ Neo4j MATCH → ✗ not found", box_red),
    (5, 3.2, "fatal_flaw:\n'persona_link not in PKG'", box_red),
    (5, 1.2, "DecisionAgent avoids\nreframing hypothesis", box_red),
]

for x, y, txt, style in steps:
    ax.text(x, y, txt, ha="center", va="center", fontsize=8.5, bbox=style)

# Arrows
for i in range(len(steps)-1):
    ax.annotate("", xy=(5, steps[i+1][1]+0.6), xytext=(5, steps[i][1]-0.6),
                arrowprops=dict(arrowstyle="->", color="#333", lw=1.5))

# Side note for B condition
ax.text(9.5, 5.2, "B(−PKG):\nno verify\n→ no fatal\n→ 50% reframe",
        ha="center", va="center", fontsize=8, color="#FF6F00",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#FFF3E0", edgecolor="#FF6F00"))
ax.annotate("", xy=(7.7, 5.2), xytext=(8.3, 5.2),
            arrowprops=dict(arrowstyle="<-", color="#FF6F00", lw=1.2))

plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig9_fatal_mechanism.png"), dpi=180, bbox_inches="tight")
print(f"Saved: {OUT}/fig9_fatal_mechanism.png")

# ────────────────────────────────────────────────
# Fig 10: Summary — why reframing rates differ across conditions
# ────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))

# Build summary data
summary = {
    "A": {"reframe_rate": 36.7, "fatal_on_reframe": 83, "pkg": True, "rag": True, "judge": True},
    "B": {"reframe_rate": 50.0, "fatal_on_reframe": 0, "pkg": False, "rag": True, "judge": True},
    "C": {"reframe_rate": 56.7, "fatal_on_reframe": 70, "pkg": True, "rag": False, "judge": True},
    "D": {"reframe_rate": 100.0, "fatal_on_reframe": None, "pkg": True, "rag": True, "judge": False},
}

x = np.arange(4)
reframe_rates = [summary[c]["reframe_rate"] for c in CONDITIONS]
bars = ax.bar(x, reframe_rates, 0.5,
              color=[COND_COLORS[c] for c in CONDITIONS],
              edgecolor="black", linewidth=0.5)

# Add fatal rate annotation
for i, c in enumerate(CONDITIONS):
    s = summary[c]
    ax.text(i, s["reframe_rate"] + 2, f"{s['reframe_rate']:.0f}%",
            ha="center", va="bottom", fontweight="bold", fontsize=13)

    # Annotation below bar
    fatal_txt = f"Fatal on reframe:\n{s['fatal_on_reframe']}%" if s['fatal_on_reframe'] is not None else "No Judge\n(single agent)"
    y_pos = -18 if c != "D" else -14
    ax.text(i, y_pos, fatal_txt, ha="center", va="top", fontsize=9, color="#555")

    # Component badges
    badges = []
    if s["pkg"]: badges.append("PKG✓")
    else: badges.append("PKG✗")
    if s["rag"]: badges.append("RAG✓")
    else: badges.append("RAG✗")
    if s["judge"]: badges.append("Judge✓")
    else: badges.append("Judge✗")
    ax.text(i, -8, " ".join(badges), ha="center", va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#f5f5f5", edgecolor="#ccc"))

ax.set_xticks(x)
ax.set_xticklabels([COND_LABELS[c] for c in CONDITIONS], fontsize=12)
ax.set_ylabel("Reframing selection rate (%)", fontsize=12)
ax.set_title("Reframing rate vs. fatal flaw mechanism across conditions", fontsize=14, fontweight="bold")
ax.set_ylim(-25, 115)
ax.axhline(y=0, color="black", linewidth=0.5)

# Add key insight as text box
insight_text = (
    "Key finding: A(Full) has the LOWEST reframing rate because:\n"
    "  1. HypothesisAgent hallucinated PKG node IDs in persona_link\n"
    "  2. JudgeAgent verified via Neo4j → 'not found' → fatal_flaw\n"
    "  3. DecisionAgent avoided reframing hypotheses with fatal flaws\n"
    "  B(−PKG): no verification possible → 0% fatal → higher reframing"
)
ax.text(0.98, 0.98, insight_text, transform=ax.transAxes,
        fontsize=8.5, va="top", ha="right",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FFF9C4", edgecolor="#F9A825", alpha=0.9))

plt.tight_layout()
plt.savefig(os.path.join(OUT, "fig10_reframing_summary.png"), dpi=180, bbox_inches="tight")
print(f"Saved: {OUT}/fig10_reframing_summary.png")
plt.close("all")
