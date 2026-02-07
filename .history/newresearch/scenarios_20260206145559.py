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
        "focus": "Conflicting evaluation — 批評家 stress test",
        "stress_target": "批評家-based hypothesis prioritisation under contradictory feedback",
        "user_input": (
            "卒業研究で提案した対話システムについて、"
            "「技術的には面白い」という評価をもらう一方で、"
            "「ユーザーにとってどんな価値があるのか分かりにくい」という意見もありました。"
            "自分としては手応えを感じているのですが、"
            "このフィードバックをどう受け止めて、研究の方向性を修正すべきか迷っています。"
        ),
    },
    "S2": {
        "id": "S2",
        "focus": "Persona-dependent research direction — PKG stress test",
        "stress_target": "PKG-driven value/skill alignment in competing alternatives",
        "user_input": (
            "卒業研究のテーマとして、"
            "「新しい対話モデルの設計」に力を入れるか、"
            "「既存の対話システムをユーザー調査で評価・分析するか」"
            "どちらを主軸にするか迷っています。"
            "どちらも興味はあるのですが、"
            "限られた時間の中でどちらを選ぶべきか判断がつきません。"
        ),
    },
    "S3": {
        "id": "S3",
        "focus": "Trend-dependent future decision — RAG stress test",
        "stress_target": "External evidence quality for uncertain future judgment",
        "user_input": (
            "対話システムの研究テーマとして、"
            "「対話の共感性や体験向上」に注力するか、"
            "「安全性や評価フレームワーク」に注力するか迷っています。"
            "どちらも重要だと思うのですが、"
            "今後の研究やキャリアを考えると、"
            "どちらに軸足を置くべきか判断材料が足りないと感じています。"
        ),
    },
}


def get_scenario(scenario_id: str) -> dict:
    """Get scenario by ID."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]
