#!/usr/bin/env python3
"""
120-run ablation experiment visualization.
Generates 8 publication-quality figures for the journal paper.

Data reading:
  - A/B/C: hypotheses.json, decision.json, judgements.json, evidence.json, final.json(response only)
  - D: final.json contains ALL keys (hypotheses, decision, judgements, evidence, final_response, markers)
"""
import os
import json
import sys
from collections import defaultdict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Config ──────────────────────────────────────────────────────
RESULTS_DIR = os.path.join(os.path.dirname(__file__), 'results', 'runs')
RUN_DATE    = '2026-02-07'
OUT_DIR     = os.path.join(os.path.dirname(__file__), 'figures_120')

COND_LABELS = {
    'A': 'A: Full\n(Multi-Agent)',
    'B': 'B: −PKG',
    'C': 'C: −RAG',
    'D': 'D: Single\n(CoT)',
}
COND_COLORS = {
    'A': '#1f77b4',   # steel blue
    'B': '#ff7f0e',   # orange
    'C': '#2ca02c',   # green
    'D': '#d62728',   # red
}
COND_HATCHES = {
    'A': '',       # solid
    'B': '///',    # diagonal
    'C': '...',    # dots
    'D': 'xxx',    # cross
}
PERSONA_NAMES = {
    'P01': 'Sugiura (47M)',
    'P05': 'Suzuki (53M)',
    'P07': 'Okada (27F)',
}

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif', 'Times New Roman', 'serif'],
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 13,
    'axes.linewidth': 0.8,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'mathtext.fontset': 'dejavuserif',
})

# ── Data Loading ────────────────────────────────────────────────
def load_all_records():
    """Load all 120 records with correct A-C vs D file structure handling."""
    runs = {}
    for cond in 'ABCD':
        cond_dir = os.path.join(RESULTS_DIR, cond)
        if not os.path.isdir(cond_dir):
            continue
        for d in sorted(os.listdir(cond_dir)):
            if not d.startswith(RUN_DATE):
                continue
            parts = d.split('__')
            if len(parts) >= 3:
                pid, sid = parts[1], parts[2]
                runs[(pid, sid, cond)] = os.path.join(cond_dir, d)

    records = []
    for (pid, sid, cond), run_path in sorted(runs.items()):
        rec = _extract_record(run_path, pid, sid, cond)
        records.append(rec)

    assert len(records) == 120, f"Expected 120 records, got {len(records)}"
    return records


def _extract_record(run_path, pid, sid, cond):
    """Extract a single record, handling the two file structures."""
    # ── Load hypothesis + decision + judgements ──
    if cond == 'D':
        with open(os.path.join(run_path, 'final.json')) as f:
            data = json.load(f)
        hyps  = data.get('hypotheses', [])
        dec   = data.get('decision', {})
        judg  = data.get('judgements', [])
    else:
        with open(os.path.join(run_path, 'hypotheses.json')) as f:
            hyps = json.load(f).get('hypotheses', [])
        with open(os.path.join(run_path, 'decision.json')) as f:
            dec = json.load(f)
        judg_path = os.path.join(run_path, 'judgements.json')
        if os.path.exists(judg_path):
            with open(judg_path) as f:
                judg = json.load(f).get('judgements', [])
        else:
            judg = []

    # ── Selected hypothesis ──
    sel_id = dec.get('selected_hypothesis_id', '')
    selected = None
    for h in hyps:
        if h.get('hypothesis_id') == sel_id:
            selected = h
            break

    is_refr   = selected.get('is_reframing', False) if selected else False
    plinks    = selected.get('persona_link', []) if selected else []
    elinks    = selected.get('evidence_link', []) if selected else []

    # ── Aggregate stats ──
    n_refr_hyps  = sum(1 for h in hyps if h.get('is_reframing', False))
    n_hyps       = len(hyps)
    n_fatal      = sum(1 for j in judg if j.get('has_fatal_flaw', False))
    refr_ratio_all = n_refr_hyps / n_hyps if n_hyps else 0.0

    # ── Confidence score (if available) ──
    confidence = selected.get('confidence', None) if selected else None

    return {
        'pid': pid, 'sid': sid, 'cond': cond,
        'is_refr': is_refr,
        'has_plink': len(plinks) > 0,
        'has_elink': len(elinks) > 0,
        'n_plinks': len(plinks),
        'n_elinks': len(elinks),
        'n_refr_hyps': n_refr_hyps,
        'n_hyps': n_hyps,
        'n_fatal_flaws': n_fatal,
        'refr_ratio_all': refr_ratio_all,
        'confidence': confidence,
    }


# ── Plotting Functions ──────────────────────────────────────────

def fig1_reframing_rate_by_condition(records):
    """Bar chart: Reframing rate per condition with exact counts."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    conds = list('ABCD')
    rates, counts, totals = [], [], []
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        n = sum(1 for r in cr if r['is_refr'])
        rates.append(100 * n / len(cr))
        counts.append(n)
        totals.append(len(cr))

    bars = ax.bar(range(4), rates, color=[COND_COLORS[c] for c in conds],
                  edgecolor='black', linewidth=0.8, width=0.6,
                  hatch=[COND_HATCHES[c] for c in conds])
    for i, (bar, cnt, tot) in enumerate(zip(bars, counts, totals)):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{cnt}/{tot} ({rates[i]:.0f}%)',
                ha='center', va='bottom', fontsize=10)

    ax.set_xticks(range(4))
    ax.set_xticklabels([COND_LABELS[c] for c in conds], fontsize=11)
    ax.set_ylabel('Reframing Rate (%)')
    ax.set_ylim(0, 118)
    ax.set_title('Selected-Hypothesis Reframing Rate by Ablation Condition',
                 fontsize=13, pad=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.axhline(50, color='grey', ls='--', lw=0.7, alpha=0.6, zorder=0)
    ax.yaxis.set_major_locator(plt.MultipleLocator(25))
    ax.yaxis.grid(True, linestyle=':', alpha=0.3)
    fig.tight_layout()
    return fig


def fig2_reframing_by_persona(records):
    """Grouped bar: Reframing rate per persona × condition."""
    fig, ax = plt.subplots(figsize=(9, 4.5))
    pids = ['P01', 'P05', 'P07']
    conds = list('ABCD')
    x = np.arange(len(pids))
    width = 0.18

    for i, c in enumerate(conds):
        vals = []
        for pid in pids:
            cr = [r for r in records if r['pid'] == pid and r['cond'] == c]
            n = sum(1 for r in cr if r['is_refr'])
            vals.append(100 * n / len(cr))
        bars = ax.bar(x + i * width, vals, width,
                      label=COND_LABELS[c].replace('\n', ' '),
                      color=COND_COLORS[c], edgecolor='black', linewidth=0.6,
                      hatch=COND_HATCHES[c])
        for j, bar in enumerate(bars):
            if vals[j] > 0:
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{vals[j]:.0f}', ha='center', va='bottom', fontsize=9)

    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels([PERSONA_NAMES[p] for p in pids], fontsize=11)
    ax.set_ylabel('Reframing Rate (%)')
    ax.set_ylim(0, 118)
    ax.set_title('Reframing Rate by Persona × Condition', fontsize=13, pad=10)
    ax.legend(loc='upper left', fontsize=9, ncol=2,
             framealpha=0.9, edgecolor='grey')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.set_major_locator(plt.MultipleLocator(25))
    ax.yaxis.grid(True, linestyle=':', alpha=0.3)
    fig.tight_layout()
    return fig


def fig3_scenario_heatmap(records):
    """Heatmap: Scenario × Condition reframing rate."""
    fig, ax = plt.subplots(figsize=(8, 6))
    scenarios = [f'S{i}' for i in range(1, 11)]
    conds = list('ABCD')

    data = np.zeros((len(scenarios), len(conds)))
    annot = [['' for _ in conds] for _ in scenarios]
    for i, sid in enumerate(scenarios):
        for j, c in enumerate(conds):
            cr = [r for r in records if r['sid'] == sid and r['cond'] == c]
            n = sum(1 for r in cr if r['is_refr'])
            data[i, j] = 100 * n / len(cr) if cr else 0
            annot[i][j] = f'{n}/{len(cr)}'

    im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)
    for i in range(len(scenarios)):
        for j in range(len(conds)):
            color = 'white' if data[i, j] < 30 or data[i, j] > 80 else 'black'
            ax.text(j, i, annot[i][j], ha='center', va='center',
                    fontsize=10, color=color, fontweight='bold')

    ax.set_xticks(range(4))
    ax.set_xticklabels([COND_LABELS[c].split('\n')[0] for c in conds])
    ax.set_yticks(range(10))
    ax.set_yticklabels(scenarios)
    ax.set_xlabel('Condition')
    ax.set_ylabel('Scenario')
    ax.set_title('Reframing Rate Heatmap: Scenario × Condition',
                 fontsize=13, pad=10)
    cbar = fig.colorbar(im, ax=ax, label='Reframing Rate (%)', shrink=0.85)
    fig.tight_layout()
    return fig


def fig4_link_rates(records):
    """Grouped bar: persona_link and evidence_link rates per condition."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    conds = list('ABCD')

    # persona_link
    plink_rates = []
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        n = sum(1 for r in cr if r['has_plink'])
        plink_rates.append(100 * n / len(cr))
    bars1 = ax1.bar(range(4), plink_rates, color=[COND_COLORS[c] for c in conds],
                    edgecolor='black', linewidth=0.6, width=0.6,
                    hatch=[COND_HATCHES[c] for c in conds])
    for bar, val in zip(bars1, plink_rates):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                 f'{val:.0f}%', ha='center', fontsize=10)
    ax1.set_xticks(range(4))
    ax1.set_xticklabels([COND_LABELS[c].split('\n')[0] for c in conds])
    ax1.set_ylabel('Presence Rate (%)')
    ax1.set_ylim(0, 118)
    ax1.set_title('(a) persona_link', fontsize=12)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.yaxis.grid(True, linestyle=':', alpha=0.3)

    # evidence_link
    elink_rates = []
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        n = sum(1 for r in cr if r['has_elink'])
        elink_rates.append(100 * n / len(cr))
    bars2 = ax2.bar(range(4), elink_rates, color=[COND_COLORS[c] for c in conds],
                    edgecolor='black', linewidth=0.6, width=0.6,
                    hatch=[COND_HATCHES[c] for c in conds])
    for bar, val in zip(bars2, elink_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                 f'{val:.0f}%', ha='center', fontsize=10)
    ax2.set_xticks(range(4))
    ax2.set_xticklabels([COND_LABELS[c].split('\n')[0] for c in conds])
    ax2.set_ylabel('Presence Rate (%)')
    ax2.set_ylim(0, 118)
    ax2.set_title('(b) evidence_link', fontsize=12)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.yaxis.grid(True, linestyle=':', alpha=0.3)

    fig.suptitle('Grounding Link Presence Rates by Condition',
                 fontsize=13, y=1.02)
    fig.tight_layout()
    return fig


def fig5_hypothesis_composition(records):
    """Stacked bar: reframing vs non-reframing hypotheses per condition."""
    fig, ax = plt.subplots(figsize=(8, 5))
    conds = list('ABCD')

    refr_avgs, nonrefr_avgs = [], []
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        avg_refr = np.mean([r['n_refr_hyps'] for r in cr])
        avg_tot  = np.mean([r['n_hyps'] for r in cr])
        refr_avgs.append(avg_refr)
        nonrefr_avgs.append(avg_tot - avg_refr)

    bars1 = ax.bar(range(4), nonrefr_avgs, color='#b0bec5', edgecolor='black',
                   linewidth=0.6, label='Non-reframing', width=0.55, hatch='...')
    bars2 = ax.bar(range(4), refr_avgs, bottom=nonrefr_avgs, color='#1565C0',
                   edgecolor='black', linewidth=0.6, label='Reframing', width=0.55)

    for i in range(4):
        total = refr_avgs[i] + nonrefr_avgs[i]
        ax.text(i, total + 0.08, f'{total:.1f}', ha='center', fontsize=10)
        ax.text(i, nonrefr_avgs[i] + refr_avgs[i]/2,
                f'{refr_avgs[i]:.1f}', ha='center', va='center',
                fontsize=10, color='white', fontweight='bold')

    ax.set_xticks(range(4))
    ax.set_xticklabels([COND_LABELS[c] for c in conds], fontsize=11)
    ax.set_ylabel('Avg. Hypotheses per Run')
    ax.set_ylim(0, 7)
    ax.set_title('Hypothesis Composition by Condition', fontsize=13, pad=10)
    ax.legend(framealpha=0.9, edgecolor='grey')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.yaxis.grid(True, linestyle=':', alpha=0.3)
    fig.tight_layout()
    return fig


def fig6_persona_scenario_detail(records):
    """3×4 heatmap: Per-persona, scenario×condition detail."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 6), sharey=True)
    pids = ['P01', 'P05', 'P07']
    conds = list('ABCD')
    scenarios = [f'S{i}' for i in range(1, 11)]

    for ax_idx, pid in enumerate(pids):
        ax = axes[ax_idx]
        data = np.zeros((10, 4))
        for i, sid in enumerate(scenarios):
            for j, c in enumerate(conds):
                cr = [r for r in records if r['pid'] == pid and r['sid'] == sid and r['cond'] == c]
                if cr:
                    data[i, j] = 1 if cr[0]['is_refr'] else 0

        im = ax.imshow(data, cmap='RdYlGn', aspect='auto', vmin=0, vmax=1)
        for i in range(10):
            for j in range(4):
                symbol = 'Y' if data[i, j] == 1 else 'N'
                color = 'white' if data[i, j] == 0 else 'black'
                ax.text(j, i, symbol, ha='center', va='center',
                        fontsize=11, color=color, fontweight='bold')

        ax.set_xticks(range(4))
        ax.set_xticklabels([c for c in conds], fontsize=10)
        ax.set_yticks(range(10))
        if ax_idx == 0:
            ax.set_yticklabels(scenarios)
        ax.set_title(PERSONA_NAMES[pid], fontsize=12)

    # Legend
    green_patch = mpatches.Patch(color='#2ca02c', label='Reframing (Y)')
    red_patch   = mpatches.Patch(color='#d62728', label='Non-reframing (N)')
    fig.legend(handles=[green_patch, red_patch], loc='lower center',
               ncol=2, fontsize=10, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle('Per-Persona Reframing Detail: Scenario × Condition',
                 fontsize=13)
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    return fig


def fig7_summary_table(records):
    """Table figure summarizing all key metrics."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.axis('off')

    conds = list('ABCD')
    col_labels = ['Metric'] + [COND_LABELS[c].replace('\n', ' ') for c in conds]

    rows = []
    # Row 1: Reframing Rate
    row = ['Reframing Rate (selected)']
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        n = sum(1 for r in cr if r['is_refr'])
        row.append(f'{n}/{len(cr)} ({100*n/len(cr):.0f}%)')
    rows.append(row)

    # Row 2: persona_link
    row = ['persona_link present']
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        n = sum(1 for r in cr if r['has_plink'])
        row.append(f'{n}/{len(cr)} ({100*n/len(cr):.0f}%)')
    rows.append(row)

    # Row 3: evidence_link
    row = ['evidence_link present']
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        n = sum(1 for r in cr if r['has_elink'])
        row.append(f'{n}/{len(cr)} ({100*n/len(cr):.0f}%)')
    rows.append(row)

    # Row 4: Avg hypotheses
    row = ['Avg hypotheses/run']
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        avg = np.mean([r['n_hyps'] for r in cr])
        row.append(f'{avg:.1f}')
    rows.append(row)

    # Row 5: Avg reframing hyps
    row = ['Avg reframing hyps']
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        avg = np.mean([r['n_refr_hyps'] for r in cr])
        row.append(f'{avg:.1f}')
    rows.append(row)

    # Row 6: Fatal flaws
    row = ['Runs with fatal flaws']
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        n = sum(1 for r in cr if r['n_fatal_flaws'] > 0)
        row.append(f'{n}/{len(cr)}')
    rows.append(row)

    table = ax.table(cellText=rows, colLabels=col_labels, loc='center',
                     cellLoc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)

    # Academic styling — alternating rows, clean header
    for j in range(5):
        table[0, j].set_facecolor('#333333')
        table[0, j].set_text_props(color='white', fontweight='bold', fontsize=10)
        table[0, j].set_edgecolor('white')
    for i in range(1, len(rows) + 1):
        table[i, 0].set_facecolor('#e8e8e8')
        table[i, 0].set_text_props(fontweight='bold', fontsize=9)
        bg = '#ffffff' if i % 2 == 1 else '#f5f5f5'
        for j in range(1, 5):
            table[i, j].set_facecolor(bg)
            table[i, j].set_text_props(fontsize=10)

    ax.set_title('Summary of Key Metrics by Condition',
                 fontsize=13, pad=20)
    fig.tight_layout()
    return fig


def fig8_condition_comparison_radar(records):
    """Radar/spider chart comparing conditions across multiple dimensions."""
    fig, ax = plt.subplots(figsize=(8, 7), subplot_kw=dict(polar=True))

    metrics = [
        'Reframing\nRate',
        'persona_link\nRate',
        'evidence_link\nRate',
        'Avg Reframing\nHyps Ratio',
        'No Fatal\nFlaws Rate',
    ]
    N = len(metrics)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close polygon

    conds = list('ABCD')
    for c in conds:
        cr = [r for r in records if r['cond'] == c]
        vals = [
            sum(1 for r in cr if r['is_refr']) / len(cr) * 100,
            sum(1 for r in cr if r['has_plink']) / len(cr) * 100,
            sum(1 for r in cr if r['has_elink']) / len(cr) * 100,
            np.mean([r['refr_ratio_all'] for r in cr]) * 100,
            sum(1 for r in cr if r['n_fatal_flaws'] == 0) / len(cr) * 100,
        ]
        vals += vals[:1]  # close polygon
        ax.plot(angles, vals, 'o-', linewidth=2, label=COND_LABELS[c].replace('\n', ' '),
                color=COND_COLORS[c])
        ax.fill(angles, vals, alpha=0.1, color=COND_COLORS[c])

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=10)
    ax.set_ylim(0, 110)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(['25', '50', '75', '100'], fontsize=8)
    ax.set_title('Multi-Dimensional Condition Comparison',
                 fontsize=13, pad=25)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.12), fontsize=9,
             framealpha=0.9, edgecolor='grey')
    fig.tight_layout()
    return fig


# ── HTML Gallery ────────────────────────────────────────────────

def generate_html_gallery(out_dir):
    """Generate an HTML page with all figures for easy browsing."""
    figs = sorted(f for f in os.listdir(out_dir) if f.endswith('.png'))
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>120-Run Ablation Results</title>
<style>
body {{ font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
h1 {{ color: #1a237e; border-bottom: 3px solid #1a237e; padding-bottom: 10px; }}
.fig {{ background: white; border-radius: 8px; padding: 16px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.fig img {{ width: 100%; max-width: 900px; display: block; margin: 0 auto; }}
.fig h3 {{ color: #37474f; margin-top: 0; }}
.summary {{ background: #e3f2fd; border-left: 4px solid #1565c0; padding: 16px; border-radius: 4px; margin: 20px 0; }}
.summary h3 {{ margin-top: 0; color: #0d47a1; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.grid .metric {{ background: white; padding: 12px; border-radius: 4px; text-align: center; }}
.grid .metric .val {{ font-size: 28px; font-weight: bold; }}
.grid .metric .label {{ font-size: 12px; color: #666; }}
</style>
</head>
<body>
<h1>120-Run Ablation Experiment Results</h1>
<p>Date: {RUN_DATE} &nbsp;|&nbsp; 3 Personas × 10 Scenarios × 4 Conditions = 120 runs</p>

<div class="summary">
<h3>Key Findings</h3>
<div class="grid">
  <div class="metric"><div class="val" style="color:#2196F3">67%</div><div class="label">A: Full (PKG+RAG+Judge)</div></div>
  <div class="metric"><div class="val" style="color:#FF9800">37%</div><div class="label">B: −PKG</div></div>
  <div class="metric"><div class="val" style="color:#4CAF50">83%</div><div class="label">C: −RAG</div></div>
  <div class="metric"><div class="val" style="color:#F44336">100%</div><div class="label">D: Single (CoT)</div></div>
</div>
</div>

"""
    for fname in figs:
        title = fname.replace('.png', '').replace('_', ' ').title()
        html += f'<div class="fig"><img src="{fname}" alt="{title}"></div>\n'

    html += """
</body>
</html>
"""
    with open(os.path.join(out_dir, 'index.html'), 'w') as f:
        f.write(html)
    print(f"HTML gallery: {os.path.join(out_dir, 'index.html')}")


# ── Main ────────────────────────────────────────────────────────

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Loading records...")
    records = load_all_records()
    print(f"Loaded {len(records)} records")

    # Validate counts
    for c in 'ABCD':
        n = sum(1 for r in records if r['cond'] == c)
        assert n == 30, f"Condition {c}: expected 30, got {n}"
    print("Validation passed: 30 runs per condition ✓")

    plot_funcs = [
        ('fig1_reframing_by_condition', fig1_reframing_rate_by_condition),
        ('fig2_reframing_by_persona', fig2_reframing_by_persona),
        ('fig3_scenario_heatmap', fig3_scenario_heatmap),
        ('fig4_link_rates', fig4_link_rates),
        ('fig5_hypothesis_composition', fig5_hypothesis_composition),
        ('fig6_persona_scenario_detail', fig6_persona_scenario_detail),
        ('fig7_summary_table', fig7_summary_table),
        ('fig8_radar_comparison', fig8_condition_comparison_radar),
    ]

    for name, func in plot_funcs:
        print(f"  Generating {name}...")
        fig = func(records)
        fig.savefig(os.path.join(OUT_DIR, f'{name}.png'),
                    bbox_inches='tight', dpi=300, facecolor='white')
        fig.savefig(os.path.join(OUT_DIR, f'{name}.pdf'),
                    bbox_inches='tight', facecolor='white')
        plt.close(fig)

    generate_html_gallery(OUT_DIR)
    print(f"\nAll {len(plot_funcs)} figures saved to {OUT_DIR}/")
    print("Done ✓")


if __name__ == '__main__':
    main()
