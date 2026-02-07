"""
ABCD Deep Comparison — richer visualisation for N=1 ablation.

Extracts qualitative/structural features directly from the JSON outputs,
not just the pre-computed metrics.csv.  Produces:
  1. Hypothesis Content Heatmap (type × condition)
  2. Information Flow Sankey-style diagram
  3. Persona Grounding Depth chart
  4. Response Qualitative Radar
  5. Trigger → Hypothesis → Decision trace table

Usage:
    python -m newresearch.visualize_deep
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

RUNS_DIR = Path(__file__).parent / "results" / "runs"
FIGURES_DIR = Path(__file__).parent / "results" / "figures"

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


# ── Font ────────────────────────────────────────────────────────────
def _setup_font():
    jp = []
    for f in fm.findSystemFonts():
        fn = f.lower()
        if any(k in fn for k in ["notosanscjk", "notosansjp", "ipag", "ipam"]):
            jp.append(f)
    if jp:
        plt.rcParams["font.family"] = fm.FontProperties(fname=jp[0]).get_name()
    else:
        plt.rcParams["font.family"] = "DejaVu Sans"


# ── Data loading ────────────────────────────────────────────────────
def _find_run_dir(cond: str) -> Path | None:
    cond_dir = RUNS_DIR / cond
    if not cond_dir.exists():
        return None
    runs = sorted(cond_dir.iterdir())
    return runs[-1] if runs else None


def _load_json(p: Path) -> dict | list | None:
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _load_all() -> dict[str, dict]:
    """Returns {cond: {context, evidence, hypotheses, judgements, decision, final}}."""
    data = {}
    for c in COND_ORDER:
        d = _find_run_dir(c)
        if not d:
            continue
        data[c] = {
            "context": _load_json(d / "context.json"),
            "evidence": _load_json(d / "evidence.json"),
            "hypotheses": _load_json(d / "hypotheses.json"),
            "judgements": _load_json(d / "judgements.json"),
            "decision": _load_json(d / "decision.json"),
            "final": _load_json(d / "final.json"),
        }
    return data


# ── Metric extractors ──────────────────────────────────────────────

def _hyp_types(hdata: dict | None) -> Counter:
    if not hdata:
        return Counter()
    return Counter(h["type"] for h in hdata.get("hypotheses", []))


def _persona_depth(hdata: dict | None) -> dict:
    """How deeply hypotheses reference PKG nodes."""
    if not hdata:
        return {"total_links": 0, "unique_nodes": set(), "linked_hyp_ratio": 0}
    hyps = hdata.get("hypotheses", [])
    total = sum(len(h.get("persona_link", [])) for h in hyps)
    nodes = set()
    linked = 0
    for h in hyps:
        pl = h.get("persona_link", [])
        if pl:
            linked += 1
            for p in pl:
                nodes.add(p.replace("pkg:", ""))
    ratio = linked / len(hyps) if hyps else 0
    return {"total_links": total, "unique_nodes": nodes, "linked_hyp_ratio": ratio}


def _evidence_depth(hdata: dict | None) -> dict:
    if not hdata:
        return {"total_links": 0, "linked_hyp_ratio": 0}
    hyps = hdata.get("hypotheses", [])
    total = sum(len(h.get("evidence_link", [])) for h in hyps)
    linked = sum(1 for h in hyps if h.get("evidence_link"))
    return {"total_links": total, "linked_hyp_ratio": linked / len(hyps) if hyps else 0}


def _obs_coverage(hdata: dict | None) -> float:
    """Fraction of observations explained by at least one hypothesis."""
    if not hdata:
        return 0
    hyps = hdata.get("hypotheses", [])
    all_explained = set()
    for h in hyps:
        all_explained.update(h.get("explains", []))
    # Count unique O/Oext
    return len(all_explained)


def _trigger_count(edata: dict | None) -> int:
    if not edata:
        return 0
    return len(edata.get("triggers", []))


def _trigger_types(edata: dict | None) -> Counter:
    if not edata:
        return Counter()
    return Counter(t["type"] for t in edata.get("triggers", []))


def _response_features(fdata: dict | None) -> dict:
    """Extract qualitative features from final response."""
    if not fdata:
        return {}
    resp = fdata.get("final_response", "")
    markers = fdata.get("markers", {})

    # Count concrete features
    option_pattern = r'[1-2AB]\.'
    options_presented = len(re.findall(option_pattern, resp))
    question_marks = resp.count("？") + resp.count("?")
    # Check for specific action suggestion (5分, メモ, etc.)
    has_concrete_action = bool(re.search(r'(5分|メモ|書き出|振り返|チェック)', resp))
    # Sentence count
    sentences = len([s for s in re.split(r'[。\n]', resp) if s.strip()])
    # H-tag references
    h_refs = len(re.findall(r'\(H\d\)', resp))
    # PKG term usage
    pkg_terms = ["実装力", "ユーザー価値", "AI技術", "対話システム", "HCI", "プログラミング"]
    pkg_term_hits = sum(1 for t in pkg_terms if t in resp)

    return {
        "char_len": len(resp),
        "sentences": sentences,
        "questions": question_marks,
        "options_presented": options_presented,
        "has_concrete_action": has_concrete_action,
        "h_refs": h_refs,
        "pkg_term_hits": pkg_term_hits,
        "empathy_count": sum(1 for v in markers.get("empathy", {}).values() if v),
        "east_count": sum(1 for k in ["easy", "attractive", "social", "timely"]
                         if markers.get("nudge", {}).get(k)),
    }


def _decision_trace(data: dict) -> dict:
    """Extract the decision reasoning chain."""
    dec = data.get("decision") or {}
    return {
        "selected": dec.get("selected_hypothesis_id", "?"),
        "contrasting": dec.get("contrasting_hypothesis_id", "?"),
        "rationale_len": len(dec.get("selection_rationale", "")),
    }


# ── Figure 1: Hypothesis Type Heatmap ──────────────────────────────
ALL_TYPES = ["value", "psychological", "evidence_gap", "skill",
             "environmental", "goal_mismatch"]
TYPE_LABELS_JP = {
    "value": "価値観",
    "psychological": "心理的",
    "evidence_gap": "証拠不足",
    "skill": "スキル",
    "environmental": "環境",
    "goal_mismatch": "目標不一致",
}


def fig1_type_heatmap(all_data: dict):
    """Hypothesis type distribution as a heatmap."""
    conds = [c for c in COND_ORDER if c in all_data]
    matrix = np.zeros((len(ALL_TYPES), len(conds)))

    for j, c in enumerate(conds):
        types = _hyp_types(all_data[c].get("hypotheses"))
        for i, t in enumerate(ALL_TYPES):
            matrix[i, j] = types.get(t, 0)

    fig, ax = plt.subplots(figsize=(8, 5))
    im = ax.imshow(matrix, cmap="YlOrRd", aspect="auto", vmin=0, vmax=2)

    ax.set_xticks(range(len(conds)))
    ax.set_xticklabels([COND_LABELS[c] for c in conds])
    ax.set_yticks(range(len(ALL_TYPES)))
    ax.set_yticklabels([f"{TYPE_LABELS_JP[t]} ({t})" for t in ALL_TYPES], fontsize=9)

    # Annotate cells
    for i in range(len(ALL_TYPES)):
        for j in range(len(conds)):
            v = int(matrix[i, j])
            ax.text(j, i, str(v), ha="center", va="center",
                    color="white" if v >= 1 else "black", fontsize=12, fontweight="bold")

    ax.set_title("Hypothesis Type Distribution by Condition", fontsize=12, fontweight="bold")
    plt.colorbar(im, ax=ax, label="Count")
    fig.tight_layout()

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_DIR / "deep_fig1_type_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [1/5] deep_fig1_type_heatmap.png")


# ── Figure 2: Information Flow (Trigger→Evidence→Hypothesis→Decision)
def fig2_info_flow(all_data: dict):
    """Visualise the information flow pipeline counts."""
    conds = [c for c in COND_ORDER if c in all_data]

    stages = ["Triggers", "Evidence", "Oext", "Hypotheses", "Obs\nExplained", "Selected\nH type"]
    fig, ax = plt.subplots(figsize=(12, 5))
    x = np.arange(len(stages))
    width = 0.18

    for i, c in enumerate(conds):
        ev = all_data[c].get("evidence") or {}
        hyp = all_data[c].get("hypotheses") or {}
        dec = all_data[c].get("decision") or {}
        hyps_list = hyp.get("hypotheses", [])
        sel_id = dec.get("selected_hypothesis_id", "")
        sel_type = ""
        for h in hyps_list:
            if h["hypothesis_id"] == sel_id:
                sel_type = h["type"]

        vals = [
            len(ev.get("triggers", [])),
            len(ev.get("evidence_items", [])),
            len(ev.get("external_observations", [])),
            len(hyps_list),
            _obs_coverage(hyp),
            ALL_TYPES.index(sel_type) + 1 if sel_type in ALL_TYPES else 0,
        ]
        offset = (i - len(conds) / 2 + 0.5) * width
        bars = ax.bar(x + offset, vals, width * 0.9,
                      label=COND_LABELS[c], color=COND_COLORS[c],
                      edgecolor="white", linewidth=0.5)
        for bar, v in zip(bars, vals):
            label_text = str(v)
            if bar.get_x() + bar.get_width() / 2 > len(stages) - 1.5:
                # Last column: show type name instead of index
                label_text = sel_type[:6] if sel_type else "?"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    label_text, ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels(stages, fontsize=9)
    ax.set_ylabel("Count / Index")
    ax.set_title("Information Flow: Trigger → Evidence → Hypothesis → Decision",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.2)
    fig.tight_layout()

    fig.savefig(FIGURES_DIR / "deep_fig2_info_flow.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [2/5] deep_fig2_info_flow.png")


# ── Figure 3: Persona Grounding Depth ──────────────────────────────
def fig3_persona_grounding(all_data: dict):
    """Radar chart: persona/evidence grounding + response quality."""
    conds = [c for c in COND_ORDER if c in all_data]

    axes_keys = [
        "pkg_links", "pkg_unique", "pkg_ratio",
        "ev_links", "ev_ratio",
        "pkg_terms_in_resp",
    ]
    axes_labels = [
        "PKG Links\n(total)", "PKG Nodes\n(unique)", "H with PKG\n(ratio)",
        "Evidence Links\n(total)", "H with Ev\n(ratio)",
        "PKG Terms\nin Response",
    ]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    angles = np.linspace(0, 2 * np.pi, len(axes_keys), endpoint=False).tolist()
    angles += angles[:1]

    for c in conds:
        pd = _persona_depth(all_data[c].get("hypotheses"))
        ed = _evidence_depth(all_data[c].get("hypotheses"))
        rf = _response_features(all_data[c].get("final"))

        values = [
            pd["total_links"],
            len(pd["unique_nodes"]),
            pd["linked_hyp_ratio"] * 5,  # scale 0-1 → 0-5
            ed["total_links"],
            ed["linked_hyp_ratio"] * 5,
            rf.get("pkg_term_hits", 0),
        ]
        values += values[:1]

        ax.plot(angles, values, "o-", label=COND_LABELS[c],
                color=COND_COLORS[c], linewidth=2, markersize=5)
        ax.fill(angles, values, alpha=0.08, color=COND_COLORS[c])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(axes_labels, fontsize=8)
    ax.set_title("Persona & Evidence Grounding Depth",
                 fontsize=12, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
    fig.tight_layout()

    fig.savefig(FIGURES_DIR / "deep_fig3_persona_grounding.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [3/5] deep_fig3_persona_grounding.png")


# ── Figure 4: Response Quality Radar ───────────────────────────────
def fig4_response_radar(all_data: dict):
    """Radar chart of response qualitative features."""
    conds = [c for c in COND_ORDER if c in all_data]

    axes_keys = [
        "questions", "options_presented", "sentences",
        "h_refs", "pkg_term_hits",
        "empathy_count", "east_count",
    ]
    axes_labels = [
        "Questions\nasked", "Options\npresented", "Sentence\ncount",
        "H-tag\nreferences", "PKG terms\nused",
        "Empathy\nmarkers", "EAST\nmarkers",
    ]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    angles = np.linspace(0, 2 * np.pi, len(axes_keys), endpoint=False).tolist()
    angles += angles[:1]

    for c in conds:
        rf = _response_features(all_data[c].get("final"))
        values = [rf.get(k, 0) for k in axes_keys]
        values += values[:1]

        ax.plot(angles, values, "o-", label=COND_LABELS[c],
                color=COND_COLORS[c], linewidth=2, markersize=5)
        ax.fill(angles, values, alpha=0.08, color=COND_COLORS[c])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(axes_labels, fontsize=8)
    ax.set_title("Response Quality Radar",
                 fontsize=12, fontweight="bold", pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1), fontsize=8)
    fig.tight_layout()

    fig.savefig(FIGURES_DIR / "deep_fig4_response_radar.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [4/5] deep_fig4_response_radar.png")


# ── Figure 5: Decision Trace Table ─────────────────────────────────
def fig5_trace_table(all_data: dict):
    """Full trace from trigger→hypothesis→decision, presented as a table."""
    conds = [c for c in COND_ORDER if c in all_data]

    row_labels = [
        "Trigger Types",
        "Trigger Count",
        "Evidence Count",
        "Oext Count",
        "Hypothesis Types",
        "PKG Links (total)",
        "PKG Unique Nodes",
        "Evidence Links",
        "Selected H (id)",
        "Selected H (type)",
        "Contrasting H (id)",
        "Contrasting H (type)",
        "Obs Explained",
        "Response Length",
        "Questions in Resp",
        "Concrete Action",
    ]

    table_data = []
    for c in conds:
        ev = all_data[c].get("evidence") or {}
        hyp = all_data[c].get("hypotheses") or {}
        dec = all_data[c].get("decision") or {}
        fin = all_data[c].get("final") or {}
        hyps_list = hyp.get("hypotheses", [])
        rf = _response_features(fin)
        pd = _persona_depth(hyp)

        sel_id = dec.get("selected_hypothesis_id", "?")
        con_id = dec.get("contrasting_hypothesis_id", "?")
        sel_type = con_type = "?"
        for h in hyps_list:
            if h["hypothesis_id"] == sel_id:
                sel_type = h["type"]
            if h["hypothesis_id"] == con_id:
                con_type = h["type"]

        trig_types = _trigger_types(ev)
        htypes = _hyp_types(hyp)

        col = [
            ", ".join(f"{k}:{v}" for k, v in trig_types.items()),
            str(len(ev.get("triggers", []))),
            str(len(ev.get("evidence_items", []))),
            str(len(ev.get("external_observations", []))),
            ", ".join(f"{k}:{v}" for k, v in htypes.items()),
            str(pd["total_links"]),
            ", ".join(sorted(pd["unique_nodes"])) or "-",
            str(_evidence_depth(hyp)["total_links"]),
            sel_id,
            sel_type,
            con_id,
            con_type,
            str(int(_obs_coverage(hyp))),
            str(rf.get("char_len", 0)),
            str(rf.get("questions", 0)),
            "Yes" if rf.get("has_concrete_action") else "No",
        ]
        table_data.append(col)

    # Transpose: rows=metrics, cols=conditions
    n_rows = len(row_labels)
    n_cols = len(conds)
    cell_text = [[table_data[j][i] for j in range(n_cols)] for i in range(n_rows)]

    fig, ax = plt.subplots(figsize=(14, max(8, n_rows * 0.45)))
    ax.axis("off")

    col_labels = [COND_LABELS[c] for c in conds]
    tbl = ax.table(cellText=cell_text, rowLabels=row_labels, colLabels=col_labels,
                   cellLoc="center", loc="center", rowLoc="right")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1.0, 1.45)

    # Header styling
    for j in range(n_cols):
        tbl[0, j].set_facecolor(COND_COLORS[conds[j]])
        tbl[0, j].set_text_props(color="white", weight="bold", fontsize=9)

    # Row label styling
    for i in range(n_rows):
        tbl[i + 1, -1].set_text_props(fontsize=8, ha="right")

    # Highlight key differences
    highlight_rows = {1, 2, 3, 5, 6, 7}  # trigger/evidence/PKG rows
    for i in range(n_rows):
        for j in range(n_cols):
            if i in highlight_rows:
                vals = [table_data[k][i] for k in range(n_cols)]
                if len(set(vals)) > 1:
                    tbl[i + 1, j].set_facecolor("#fff3cd")

    ax.set_title("Decision Trace: Trigger → Hypothesis → Decision → Response",
                 fontsize=13, fontweight="bold", pad=15)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "deep_fig5_trace_table.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  [5/5] deep_fig5_trace_table.png")


# ── Main ────────────────────────────────────────────────────────────
def main():
    _setup_font()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading run data...")
    all_data = _load_all()
    if not all_data:
        print("No run data found!")
        return

    print(f"Found conditions: {list(all_data.keys())}")
    print()

    fig1_type_heatmap(all_data)
    fig2_info_flow(all_data)
    fig3_persona_grounding(all_data)
    fig4_response_radar(all_data)
    fig5_trace_table(all_data)

    print(f"\nAll deep figures saved to {FIGURES_DIR}/")

    # Print qualitative summary
    _print_qualitative(all_data)


def _print_qualitative(all_data: dict):
    """Print a qualitative analysis summary."""
    print("\n" + "=" * 70)
    print("QUALITATIVE ANALYSIS SUMMARY")
    print("=" * 70)

    for c in COND_ORDER:
        if c not in all_data:
            continue
        d = all_data[c]
        ev = d.get("evidence") or {}
        hyp = d.get("hypotheses") or {}
        dec = d.get("decision") or {}
        fin = d.get("final") or {}
        pd = _persona_depth(hyp)
        ed = _evidence_depth(hyp)
        rf = _response_features(fin)
        hyps = hyp.get("hypotheses", [])

        sel_id = dec.get("selected_hypothesis_id", "?")
        con_id = dec.get("contrasting_hypothesis_id", "?")
        sel_h = con_h = None
        for h in hyps:
            if h["hypothesis_id"] == sel_id:
                sel_h = h
            if h["hypothesis_id"] == con_id:
                con_h = h

        print(f"\n--- {COND_LABELS[c]} ---")
        print(f"  Triggers: {len(ev.get('triggers', []))}, "
              f"Evidence: {len(ev.get('evidence_items', []))}, "
              f"Oext: {len(ev.get('external_observations', []))}")
        print(f"  PKG links: {pd['total_links']} ({len(pd['unique_nodes'])} unique nodes)")
        print(f"  Ev links: {ed['total_links']}")
        print(f"  Types: {dict(_hyp_types(hyp))}")
        if sel_h:
            print(f"  Selected: {sel_id} ({sel_h['type']})")
            print(f"    '{sel_h['statement'][:80]}...'")
        if con_h:
            print(f"  Contrast: {con_id} ({con_h['type']})")
            print(f"    '{con_h['statement'][:80]}...'")
        print(f"  Response: {rf.get('char_len', 0)} chars, "
              f"{rf.get('questions', 0)} questions, "
              f"action={'Yes' if rf.get('has_concrete_action') else 'No'}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
