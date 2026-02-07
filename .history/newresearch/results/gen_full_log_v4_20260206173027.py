#!/usr/bin/env python3
"""v4 全12ラン（S1-S3 × A-D）の完全ログを1ファイルにまとめる"""
import json, os, textwrap

BASE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(BASE, "runs")

# v4 ランディレクトリのマッピング
DIRS = {
    ("S1", "A"): "A/2026-02-06T170048__S1__PKG1_RAG1_JUDGE1",
    ("S1", "B"): "B/2026-02-06T170208__S1__PKG0_RAG1_JUDGE1",
    ("S1", "C"): "C/2026-02-06T170311__S1__PKG1_RAG0_JUDGE1",
    ("S1", "D"): "D/2026-02-06T170409__S1__SINGLE",
    ("S2", "A"): "A/2026-02-06T171631__S2__PKG1_RAG1_JUDGE1",
    ("S2", "B"): "B/2026-02-06T171740__S2__PKG0_RAG1_JUDGE1",
    ("S2", "C"): "C/2026-02-06T171848__S2__PKG1_RAG0_JUDGE1",
    ("S2", "D"): "D/2026-02-06T171943__S2__SINGLE",
    ("S3", "A"): "A/2026-02-06T172036__S3__PKG1_RAG1_JUDGE1",
    ("S3", "B"): "B/2026-02-06T172145__S3__PKG0_RAG1_JUDGE1",
    ("S3", "C"): "C/2026-02-06T172248__S3__PKG1_RAG0_JUDGE1",
    ("S3", "D"): "D/2026-02-06T172346__S3__SINGLE",
}

SCENARIO_LABELS = {
    "S1": "本物志向 vs blind-spot（築地）",
    "S2": "効率固執 vs serendipity（旅行計画）",
    "S3": "金沢東茶屋街 expertise vs fresh data",
}

CONDITION_LABELS = {
    "A": "Full（PKG✓ RAG✓ 批評家✓）",
    "B": "−PKG（PKG✗ RAG✓ 批評家✓）",
    "C": "−RAG（PKG✓ RAG✗ 批評家✓）",
    "D": "SingleAgent / CoT",
}


def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None


def load_text(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except Exception:
        return "(not found)"


def fmt_observations(ctx):
    """context.json → 観察一覧"""
    lines = []
    obs = ctx.get("observations", [])
    for o in obs:
        tag = o.get("id", "?")
        desc = o.get("description", "")
        lines.append(f"  {tag}: {desc}")
    return "\n".join(lines) if lines else "  (なし)"


def fmt_assumptions(ctx):
    """context.json → 仮定一覧"""
    lines = []
    asm = ctx.get("assumptions", [])
    for a in asm:
        tag = a.get("id", "?")
        desc = a.get("description", "")
        status = a.get("status", "")
        lines.append(f"  {tag}: {desc}  [{status}]")
    return "\n".join(lines) if lines else "  (なし)"


def fmt_evidence(ev):
    """evidence.json → 外部観察"""
    if not ev:
        return "  (RAG無効 or 結果0件)"
    oext = ev.get("external_observations", [])
    if not oext:
        return "  (RAG無効 or 結果0件)"
    lines = []
    for o in oext:
        tag = o.get("id", "?")
        desc = o.get("description", "")
        lines.append(f"  {tag}: {desc}")
    return "\n".join(lines) if lines else "  (なし)"


def fmt_hypotheses(hyp):
    """hypotheses.json → 仮説一覧"""
    lines = []
    hlist = hyp.get("hypotheses", [])
    for h in hlist:
        tag = h.get("id", "?")
        cat = h.get("category", "?")
        desc = h.get("description", "")
        is_ref = h.get("is_reframing", False)
        explains = h.get("explains", [])
        persona = h.get("persona_link", [])
        marker = " ★REFRAMING" if is_ref else ""
        lines.append(f"  {tag} [{cat}]{marker}: {desc}")
        lines.append(f"    explains: {explains}  persona_link: {persona}")
    return "\n".join(lines) if lines else "  (なし)"


def fmt_judgements(jdg):
    """judgements.json → 批評"""
    if not jdg:
        return "  (批評家なし / Condition D)"
    reviews = jdg.get("reviews", [])
    if not reviews:
        return "  (批評なし)"
    lines = []
    for r in reviews:
        hid = r.get("hypothesis_id", "?")
        lines.append(f"  --- {hid} ---")
        # plausibility
        p = r.get("plausibility", {})
        if isinstance(p, dict):
            lines.append(f"    plausibility: {p.get('score','?')}/5  {p.get('rationale','')}")
        # novelty
        n = r.get("novelty", {})
        if isinstance(n, dict):
            lines.append(f"    novelty: {n.get('score','?')}/5  {n.get('rationale','')}")
        # fatal_flaws
        ff = r.get("fatal_flaws", [])
        if ff:
            lines.append(f"    fatal_flaws: {ff}")
        else:
            lines.append(f"    fatal_flaws: (none)")
        # missing_evidence
        me = r.get("missing_evidence", [])
        if me:
            lines.append(f"    missing_evidence: {me}")
    return "\n".join(lines)


def fmt_decision(dec):
    """decision.json → 選択"""
    if not dec:
        return "  (なし)"
    lines = []
    sel = dec.get("selected", "?")
    con = dec.get("contrasting", "?")
    rat = dec.get("rationale", "")
    opt1 = dec.get("option_1", "")
    opt2 = dec.get("option_2", "")
    lines.append(f"  selected: {sel}  contrasting: {con}")
    lines.append(f"  rationale: {rat}")
    if opt1:
        lines.append(f"  option 1: {opt1}")
    if opt2:
        lines.append(f"  option 2: {opt2}")
    return "\n".join(lines)


def process_run(scenario, condition):
    rel = DIRS.get((scenario, condition))
    if not rel:
        return f"  (ディレクトリ不明)\n"
    d = os.path.join(RUNS, rel)

    ctx = load_json(os.path.join(d, "context.json"))
    ev = load_json(os.path.join(d, "evidence.json"))
    hyp = load_json(os.path.join(d, "hypotheses.json"))
    jdg = load_json(os.path.join(d, "judgements.json"))
    dec = load_json(os.path.join(d, "decision.json"))
    resp = load_text(os.path.join(d, "response.txt"))

    parts = []

    # 1. 観察
    parts.append("【観察 (Observations)】")
    if ctx:
        parts.append(fmt_observations(ctx))
    else:
        parts.append("  (context.json not found)")

    # 2. 仮定
    parts.append("")
    parts.append("【仮定 (Assumptions)】")
    if ctx:
        parts.append(fmt_assumptions(ctx))
    else:
        parts.append("  (context.json not found)")

    # 3. 外部観察
    parts.append("")
    parts.append("【外部観察 (External Observations)】")
    parts.append(fmt_evidence(ev))

    # 4. 仮説
    parts.append("")
    parts.append("【仮説 (Hypotheses)】")
    if hyp:
        parts.append(fmt_hypotheses(hyp))
    else:
        parts.append("  (hypotheses.json not found)")

    # 5. 批評
    parts.append("")
    parts.append("【批評 (Judgements)】")
    parts.append(fmt_judgements(jdg))

    # 6. 決定
    parts.append("")
    parts.append("【決定 (Decision)】")
    parts.append(fmt_decision(dec))

    # 7. 最終応答
    parts.append("")
    parts.append("【最終応答 (Response)】")
    parts.append(resp)

    return "\n".join(parts)


def main():
    out_lines = []
    out_lines.append("=" * 80)
    out_lines.append("v4 全12ラン 完全ログ")
    out_lines.append(f"生成日: 2026-02-06")
    out_lines.append("=" * 80)
    out_lines.append("")

    # サマリ表
    out_lines.append("■ クロスサマリ")
    out_lines.append("-" * 60)
    for s in ["S1", "S2", "S3"]:
        out_lines.append(f"  {s} ({SCENARIO_LABELS[s]}):")
        for c in ["A", "B", "C", "D"]:
            dec = load_json(os.path.join(RUNS, DIRS[(s, c)], "decision.json"))
            sel = dec.get("selected", "?") if dec else "?"
            con = dec.get("contrasting", "?") if dec else "?"
            # check reframing
            hyp = load_json(os.path.join(RUNS, DIRS[(s, c)], "hypotheses.json"))
            ref_mark = ""
            if hyp:
                for h in hyp.get("hypotheses", []):
                    if h.get("id") == sel and h.get("is_reframing"):
                        ref_mark = "★"
            out_lines.append(f"    {c} ({CONDITION_LABELS[c]}): selected={sel}{ref_mark}  contrasting={con}")
        out_lines.append("")
    out_lines.append("")

    # 各ラン詳細
    for s in ["S1", "S2", "S3"]:
        out_lines.append("#" * 80)
        out_lines.append(f"# シナリオ {s}: {SCENARIO_LABELS[s]}")
        out_lines.append("#" * 80)
        out_lines.append("")
        for c in ["A", "B", "C", "D"]:
            out_lines.append("=" * 70)
            out_lines.append(f"条件 {c}: {CONDITION_LABELS[c]}")
            out_lines.append(f"ディレクトリ: {DIRS[(s, c)]}")
            out_lines.append("=" * 70)
            out_lines.append("")
            out_lines.append(process_run(s, c))
            out_lines.append("")
            out_lines.append("")

    output = "\n".join(out_lines)
    outpath = os.path.join(BASE, "v4_full_log.txt")
    with open(outpath, "w") as f:
        f.write(output)
    print(f"Written: {outpath}  ({len(output)} chars)")


if __name__ == "__main__":
    main()
