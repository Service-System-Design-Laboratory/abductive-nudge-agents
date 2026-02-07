"""
Scenarios, fixed persona, and PKG data for the experiment.
3 scenarios × 1 fixed persona.
"""
from __future__ import annotations
from newresearch.schemas import Persona, PKGData, PKGNode, PKGEdge


# ── Fixed Persona ──────────────────────────────────────────────────

PERSONA = Persona(
    persona_id="P1",
    name="田中 翔太",
    summary=(
        "学部4年生（情報工学・AI専攻）。HCIと対話システムに興味があり、"
        "実装力が強み。研究の社会的意義や将来性に漠然とした不安を感じている。"
        "趣味はプログラミングとボードゲーム。内向的だが少人数の議論は好む。"
    ),
    pkg=PKGData(
        enabled=True,
        nodes=[
            PKGNode(id="n1", label="HCI", type="interest", weight=0.9),
            PKGNode(id="n2", label="対話システム", type="interest", weight=0.85),
            PKGNode(id="n3", label="実装力", type="skill", weight=0.9),
            PKGNode(id="n4", label="プログラミング", type="skill", weight=0.85),
            PKGNode(id="n5", label="研究の意義", type="concern", weight=0.8),
            PKGNode(id="n6", label="将来性への不安", type="concern", weight=0.75),
            PKGNode(id="n7", label="ユーザー価値の重視", type="value", weight=0.8),
            PKGNode(id="n8", label="ボードゲーム", type="interest", weight=0.5),
            PKGNode(id="n9", label="少人数の議論", type="interest", weight=0.6),
            PKGNode(id="n10", label="AI技術動向", type="interest", weight=0.7),
        ],
        edges=[
            PKGEdge(src="n1", dst="n2", rel="related_to"),
            PKGEdge(src="n2", dst="n3", rel="requires"),
            PKGEdge(src="n3", dst="n4", rel="is_a"),
            PKGEdge(src="n5", dst="n6", rel="causes"),
            PKGEdge(src="n1", dst="n7", rel="motivates"),
            PKGEdge(src="n7", dst="n5", rel="conflicts_with"),
            PKGEdge(src="n10", dst="n6", rel="amplifies"),
        ],
    ),
)


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
            "最近、仕事でAIツールを導入するプロジェクトを任されたが、"
            "周囲の反応が冷たく、自分のやり方が間違っているのか不安になっている。"
        ),
    },
    "S3": {
        "id": "S3",
        "focus": "External-knowledge-dependent",
        "stress_target": "RAG evidence quality",
        "user_input": (
            "地方に移住して農業をやりたいと漠然と思っているが、"
            "収入や生活の現実がわからず踏み出せない。"
        ),
    },
}


def get_scenario(scenario_id: str) -> dict:
    """Get scenario by ID."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]
