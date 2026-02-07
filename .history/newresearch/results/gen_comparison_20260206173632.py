#!/usr/bin/env python3
"""Generate comparison files for all scenarios."""
import json, glob, os

RESULTS_DIR = os.path.dirname(os.path.abspath(__file__))
RUNS_DIR = os.path.join(RESULTS_DIR, "runs")

def gen_scenario(scenario_id):
    output = ''
    for cond in ['A','B','C','D']:
        runs = sorted(glob.glob(os.path.join(RUNS_DIR, cond, f'*{scenario_id}*')))
        if not runs:
            continue
        run_dir = runs[-1]
        output += '=' * 70 + '\n'
        output += f'条件 {cond}\n'
        output += '=' * 70 + '\n\n'

        # context
        ctx_path = os.path.join(run_dir, 'context.json')
        if os.path.exists(ctx_path):
            raw = json.load(open(ctx_path))
            obs_list = raw.get('observations', []) if isinstance(raw, dict) else raw
            output += '【観察 (Observations)】\n'
            for o in obs_list:
                output += f"  {o['id']}: {o['text']}\n"
            asm_list = raw.get('assumptions', []) if isinstance(raw, dict) else []
            output += '\n【仮定 (Assumptions)】\n'
            for a in asm_list:
                st = a.get('status','')
                output += f"  {a['id']}: {a['text']}  [{st}]\n"
            output += '\n'

        # evidence
        ev_path = os.path.join(run_dir, 'evidence.json')
        if os.path.exists(ev_path):
            ev = json.load(open(ev_path))
            exts = ev.get('external_observations', []) if isinstance(ev, dict) else []
            if exts:
                output += '【外部観察 (External Observations)】\n'
                for e in exts:
                    output += f"  {e['id']}: {e['text']}\n"
                output += '\n'
            else:
                output += '【外部観察】なし (RAG無効 or 結果0件)\n\n'
        else:
            output += '【外部観察】なし\n\n'

        # hypotheses
        hyp_path = os.path.join(run_dir, 'hypotheses.json')
        if os.path.exists(hyp_path):
            raw = json.load(open(hyp_path))
            hyp_list = raw.get('hypotheses', raw) if isinstance(raw, dict) else raw
            output += '【仮説 (Hypotheses)】\n'
            for h in hyp_list:
                hid = h['hypothesis_id']
                ht = h.get('type','')
                ref = ' ★REFRAMING' if h.get('is_reframing') else ''
                output += f"  {hid} [{ht}]{ref}: {h['statement']}\n"
                output += f"    explains: {h.get('explains',[])}  persona_link: {h.get('persona_link',[])}\n"
            output += '\n'

        # decision
        dec_path = os.path.join(run_dir, 'decision.json')
        if os.path.exists(dec_path):
            dec = json.load(open(dec_path))
            output += '【決定 (Decision)】\n'
            output += f"  selected: {dec.get('selected_hypothesis_id','')}  contrasting: {dec.get('contrasting_hypothesis_id','')}\n"
            output += f"  rationale: {dec.get('selection_rationale','')}\n"
            uf = dec.get('user_facing_frame',{})
            opts = uf.get('options',[])
            for i,op in enumerate(opts):
                output += f"  option {i+1}: {op}\n"
            output += '\n'

        # response
        resp_path = os.path.join(run_dir, 'response.txt')
        if os.path.exists(resp_path):
            resp = open(resp_path).read().strip()
            output += '【最終応答】\n'
            output += resp + '\n'
        output += '\n\n'
    return output


def gen_cross_summary():
    """Generate a cross-scenario summary table."""
    output = '=' * 70 + '\n'
    output += '横断比較サマリー (全シナリオ × 全条件)\n'
    output += '=' * 70 + '\n\n'

    for scenario_id in ['S1','S2','S3']:
        output += f'--- {scenario_id} ---\n'
        output += f'{"条件":<6} {"selected":<12} {"contrasting":<14} {"selected仮説の要約"}\n'
        output += '-' * 70 + '\n'
        for cond in ['A','B','C','D']:
            runs = sorted(glob.glob(os.path.join(RUNS_DIR, cond, f'*{scenario_id}*')))
            if not runs:
                output += f'{cond:<6} (no run)\n'
                continue
            run_dir = runs[-1]
            dec_path = os.path.join(run_dir, 'decision.json')
            hyp_path = os.path.join(run_dir, 'hypotheses.json')
            if not os.path.exists(dec_path):
                output += f'{cond:<6} (no decision)\n'
                continue
            dec = json.load(open(dec_path))
            sel = dec.get('selected_hypothesis_id','?')
            con = dec.get('contrasting_hypothesis_id','?')

            # find selected hypothesis statement
            stmt = ''
            if os.path.exists(hyp_path):
                raw = json.load(open(hyp_path))
                hyp_list = raw.get('hypotheses', raw) if isinstance(raw, dict) else raw
                for h in hyp_list:
                    if h['hypothesis_id'] == sel:
                        s = h['statement']
                        ref = '★' if h.get('is_reframing') else ''
                        stmt = ref + (s[:60] + '...' if len(s) > 60 else s)
                        break
            output += f'{cond:<6} {sel:<12} {con:<14} {stmt}\n'
        output += '\n'
    return output


if __name__ == '__main__':
    for sid in ['S1','S2','S3']:
        text = gen_scenario(sid)
        path = os.path.join(RESULTS_DIR, f'{sid}_comparison_v4.txt')
        with open(path, 'w') as f:
            f.write(text)
        print(f'{sid}: {len(text)} chars -> {path}')

    summary = gen_cross_summary()
    spath = os.path.join(RESULTS_DIR, 'cross_summary_v4.txt')
    with open(spath, 'w') as f:
        f.write(summary)
    print(f'Summary: {len(summary)} chars -> {spath}')
