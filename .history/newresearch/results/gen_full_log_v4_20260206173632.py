#!/usr/bin/env python3
"""v4 全12ラン（S1-S3 × A-D）の完全ログを1ファイルにまとめる"""
import json, os

BASE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(BASE, "runs")

DIRS = {
    ("S1","A"): "A/2026-02-06T170048__S1__PKG1_RAG1_JUDGE1",
    ("S1","B"): "B/2026-02-06T170208__S1__PKG0_RAG1_JUDGE1",
    ("S1","C"): "C/2026-02-06T170311__S1__PKG1_RAG0_JUDGE1",
    ("S1","D"): "D/2026-02-06T170409__S1__SINGLE",
    ("S2","A"): "A/2026-02-06T171631__S2__PKG1_RAG1_JUDGE1",
    ("S2","B"): "B/2026-02-06T171740__S2__PKG0_RAG1_JUDGE1",
    ("S2","C"): "C/2026-02-06T171848__S2__PKG1_RAG0_JUDGE1",
    ("S2","D"): "D/2026-02-06T171943__S2__SINGLE",
    ("S3","A"): "A/2026-02-06T172036__S3__PKG1_RAG1_JUDGE1",
    ("S3","B"): "B/2026-02-06T172145__S3__PKG0_RAG1_JUDGE1",
    ("S3","C"): "C/2026-02-06T172248__S3__PKG1_RAG0_JUDGE1",
    ("S3","D"): "D/2026-02-06T172346__S3__SINGLE",
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
    except:
        return None

def load_text(path):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except:
        return "(not found)"

def fmt_observations(ctx):
    if not ctx: return "  (なし)"
    lines = []
    for o in ctx.get("observations", []):
        lines.append(f"  {o.get('id','?')}: {o.get('text','')}")
    return "\n".join(lines) or "  (なし)"

def fmt_assumptions(ctx):
    if not ctx: return "  (なし)"
    lines = []
    for a in ctx.get("assumptions", []):
        lines.append(f"  {a.get('id','?')}: {a.get('text','')}  [{a.get('status','')}]")
    return "\n".join(lines) or "  (なし)"

def fmt_evidence(ev):
    if not ev: return "  (RAG無効 or 結果0件)"
    parts = []
    triggers = ev.get("triggers", [])
    if triggers:
        parts.append("  [トリガー]")
        for t in triggers:
            parts.append(f"    - {t.get('type','')}: {t.get('text','')}")
    queries = ev.get("rag_queries", [])
    if queries:
        parts.append("  [RAGクエリ]")
        for q in queries:
            parts.append(f"    - {q}")
    items = ev.get("evidence_items", [])
    if items:
        parts.append("  [検索結果]")
        for it in items:
            parts.append(f"    rank{it.get('rank','?')}: {it.get('title','')} | {it.get('snippet','')[:150]}")
    oext = ev.get("external_observations", [])
    if oext:
        parts.append("  [外部観察 Oext]")
        for o in oext:
            parts.append(f"    {o.get('id','?')}: {o.get('text','')}")
    notes = ev.get("notes", "")
    if notes:
        parts.append(f"  [notes] {notes}")
    if not parts:
        return "  (RAG無効 or 結果0件)"
    return "\n".join(parts)

def fmt_hypotheses(hyp):
    if not hyp: return "  (なし)"
    lines = []
    for h in hyp.get("hypotheses", []):
        hid = h.get("hypothesis_id", "?")
        htype = h.get("type", "?")
        stmt = h.get("statement", "")
        mechanism = h.get("mechanism", "")
        is_ref = h.get("is_reframing", False)
        explains = h.get("explains", [])
        persona = h.get("persona_link", [])
        ev_link = h.get("evidence_link", [])
        preds = h.get("predictions", [])
        disc_q = h.get("discriminating_questions", [])
        marker = " ★REFRAMING" if is_ref else ""
        lines.append(f"  {hid} [{htype}]{marker}")
        lines.append(f"    statement: {stmt}")
        lines.append(f"    mechanism: {mechanism}")
        lines.append(f"    explains: {explains}")
        lines.append(f"    persona_link: {persona}  evidence_link: {ev_link}")
        if preds:
            lines.append(f"    predictions: {preds}")
        if disc_q:
            lines.append(f"    discriminating_questions: {disc_q}")
        lines.append("")
    return "\n".join(lines)

def fmt_judgements(jdg):
    if not jdg: return "  (批評家なし / Condition D)"
    reviews = jdg.get("judgements", [])
    if not reviews: return "  (批評なし)"
    lines = []
    for r in reviews:
        hid = r.get("hypothesis_id", "?")
        diag = r.get("diagnosis", {})
        rat = r.get("rationale", "")
        lines.append(f"  --- {hid} ---")
        if isinstance(diag, dict):
            ff = diag.get("fatal_flaws", [])
            ec = diag.get("explains_confirmed", [])
            ka = diag.get("key_assumptions", [])
            bdq = diag.get("best_discriminating_question", "")
            test = diag.get("testability_notes", "")
            safety = diag.get("safety_risk_notes", "")
            lines.append(f"    fatal_flaws: {ff if ff else '(none)'}")
            lines.append(f"    explains_confirmed: {ec}")
            if ka:
                lines.append(f"    key_assumptions: {ka}")
            if bdq:
                lines.append(f"    best_discriminating_question: {bdq}")
            if test:
                lines.append(f"    testability: {test}")
            if safety:
                lines.append(f"    safety_risk: {safety}")
        lines.append(f"    rationale: {rat}")
        lines.append("")
    return "\n".join(lines)

def fmt_decision(dec):
    if not dec: return "  (なし)"
    lines = []
    sel = dec.get("selected_hypothesis_id", dec.get("selected", "?"))
    con = dec.get("contrasting_hypothesis_id", dec.get("contrasting", "?"))
    rat = dec.get("selection_rationale", dec.get("rationale", ""))
    lines.append(f"  selected: {sel}  contrasting: {con}")
    lines.append(f"  rationale: {rat}")
    frame = dec.get("user_facing_frame", {})
    if frame:
        opts = frame.get("options", [])
        qs = frame.get("questions", [])
        if opts:
            for i, o in enumerate(opts, 1):
                lines.append(f"  option {i}: {o}")
        if qs:
            for i, q in enumerate(qs, 1):
                lines.append(f"  question {i}: {q}")
    return "\n".join(lines)

def process_run(scenario, condition):
    rel = DIRS.get((scenario, condition))
    if not rel: return "(ディレクトリ不明)"
    d = os.path.join(RUNS, rel)
    ctx = load_json(os.path.join(d, "context.json"))
    ev  = load_json(os.path.join(d, "evidence.json"))
    hyp = load_json(os.path.join(d, "hypotheses.json"))
    jdg = load_json(os.path.join(d, "judgements.json"))
    dec = load_json(os.path.join(d, "decision.json"))
    resp = load_text(os.path.join(d, "response.txt"))

    parts = []
    parts.append("【観察 (Observations)】")
    parts.append(fmt_observations(ctx))
    parts.append("")
    parts.append("【仮定 (Assumptions)】")
    parts.append(fmt_assumptions(ctx))
    parts.append("")
    parts.append("【外部観察・エビデンス (Evidence / External Observations)】")
    parts.append(fmt_evidence(ev))
    parts.append("")
    parts.append("【仮説 (Hypotheses)】")
    parts.append(fmt_hypotheses(hyp))
    parts.append("")
    parts.append("【批評 (Judgements)】")
    parts.append(fmt_judgements(jdg))
    parts.append("")
    parts.append("【決定 (Decision)】")
    parts.append(fmt_decision(dec))
    parts.append("")
    parts.append("【最終応答 (Response)】")
    parts.append(resp)
    return "\n".join(parts)

def main():
    out = []
    out.append("=" * 80)
    out.append("v4 全12ラン 完全ログ")
    out.append("生成日: 2026-02-06")
    out.append("=" * 80)
    out.append("")

    # クロスサマリ
    out.append("■ クロスサマリ")
    out.append("-" * 60)
    for s in ["S1","S2","S3"]:
        out.append(f"  {s} ({SCENARIO_LABELS[s]}):")
        for c in ["A","B","C","D"]:
            dec = load_json(os.path.join(RUNS, DIRS[(s,c)], "decision.json"))
            sel = dec.get("selected_hypothesis_id", dec.get("selected","?")) if dec else "?"
            con = dec.get("contrasting_hypothesis_id", dec.get("contrasting","?")) if dec else "?"
            hyp = load_json(os.path.join(RUNS, DIRS[(s,c)], "hypotheses.json"))
            ref = ""
            if hyp:
                for h in hyp.get("hypotheses",[]):
                    if h.get("hypothesis_id") == sel and h.get("is_reframing"):
                        ref = "★"
            out.append(f"    {c} ({CONDITION_LABELS[c]}): selected={sel}{ref}  contrasting={con}")
        out.append("")
    out.append("")

    for s in ["S1","S2","S3"]:
        out.append("#" * 80)
        out.append(f"# シナリオ {s}: {SCENARIO_LABELS[s]}")
        out.append("#" * 80)
        out.append("")
        for c in ["A","B","C","D"]:
            out.append("=" * 70)
            out.append(f"条件 {c}: {CONDITION_LABELS[c]}")
            out.append(f"ディレクトリ: {DIRS[(s,c)]}")
            out.append("=" * 70)
            out.append("")
            out.append(process_run(s, c))
            out.append("")
            out.append("")

    text = "\n".join(out)
    outpath = os.path.join(BASE, "v4_full_log.txt")
    with open(outpath, "w") as f:
        f.write(text)
    print(f"Written: {outpath}  ({len(text)} chars, {text.count(chr(10))} lines)")

if __name__ == "__main__":
    main()
