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
        "focus": "Ambiguity / Information gap",
        "stress_target": "Trigger extraction, multiple plausible hypotheses",
        "user_input": (
            "卒業研究を進めているが、テーマに自信が持てず、"
            "このまま大学院に進むべきか、それとも別の道を考えるべきか迷っている。"
        ),
    },
    "S2": {
        "id": "S2",
        "focus": "Persona-dependent concern",
        "stress_target": "PKG utilisation, persona_alignment",
        "user_input": (
            "研究室でチーム開発のリーダーを任されたが、"
            "メンバーとの進め方で意見が合わず、自分のやり方が間違っているのか不安になっている。"
            "自分は実装が得意なタイプだけど、リーダーとしてどう振る舞えばいいかわからない。"
        ),
    },
    "S3": {
        "id": "S3",
        "focus": "External-knowledge-dependent",
        "stress_target": "RAG evidence quality",
        "user_input": (
            "対話システムの研究をしているが、最近のLLMの進歩が速すぎて、"
            "自分の研究テーマがすぐに陳腐化するのではないかと不安を感じている。"
            "HCI的なアプローチに価値があるのか、技術追従すべきなのか迷っている。"
        ),
    },
}


def get_scenario(scenario_id: str) -> dict:
    """Get scenario by ID."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]
