"""
Scenarios and persona loading for the experiment.
3 scenarios × 1 fixed persona (loaded from Neo4j).
"""
from __future__ import annotations
from newresearch.neo4j_pkg import load_persona_from_neo4j


def get_persona(persona_id: str = "P1"):
    """Load persona + PKG from Neo4j."""
    return load_persona_from_neo4j(persona_id)


# ── Scenarios ──────────────────────────────────────────────────────

SCENARIOS = {
    "S1": {
        "id": "S1",
        "focus": "Strong identity vs blind-spot collision — PKG × RAG integration test",
        "stress_target": "PKG-grounded identity expansion via external counter-evidence (RAG)",
        "user_input": (
            "ガイドブックに載っているような場所には一切興味がないんだ。"
            "地元の人しか知らない、看板も出ていないような"
            "『本物の生活』が残っている場所だけを歩きたい。"
            "観光客向けの演出はもうお腹いっぱいだよ。"
        ),
    },
    "S2": {
        "id": "S2",
        "focus": "Efficiency fixation vs serendipity — Nudge × Trajectory test",
        "stress_target": "Abductive anomaly detection on efficiency-as-satisfaction premise + nudge-based reframing",
        "user_input": (
            "今回の3日間の旅行は分刻みでスケジュールを組んだよ。"
            "Googleマップで移動時間を計算して、"
            "最も効率的に主要スポットを回れるルートを確立した。"
            "あとはこれを完璧に実行するだけだ。"
            "何か見落としている効率化のポイントはあるかな？"
        ),
    },
    "S3": {
        "id": "S3",
        "focus": "Expert knowledge vs fresh data friction — RAG × Justification test",
        "stress_target": "External evidence quality for challenging user expertise + critic-based contrast framing",
        "user_input": (
            "伝統建築を見に金沢へ行くつもりだ。"
            "あそこは江戸時代の風情が一番よく残っている街だからね。"
            "ひがし茶屋街のあの街並みこそが、"
            "日本の美の極みだと思っているんだ。"
        ),
    },
}


def get_scenario(scenario_id: str) -> dict:
    """Get scenario by ID."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]
