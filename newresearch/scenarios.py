"""
Scenarios and persona loading for the experiment.
10 scenarios × 3 personas (loaded from Neo4j).
"""
from __future__ import annotations
from newresearch.neo4j_pkg import load_persona_from_neo4j


# ── Persona IDs available for this experiment ─────────────────────────────

PERSONA_IDS = ["P01", "P05", "P07"]


def get_persona(persona_id: str = "P01"):
    """Load persona + PKG from Neo4j."""
    return load_persona_from_neo4j(persona_id)


# ── Scenarios (10) ─────────────────────────────────────────────────
# S1-S3: original scenarios (preserved)
# S4-S10: new scenarios extending the same cognitive-bias patterns
#
# Bias categories:
#   Authenticity fixation (S1, S4)    — "authentic vs staged"
#   Efficiency fixation   (S2, S5)    — "optimization vs serendipity"
#   Expert knowledge      (S3, S6)    — "expert knowledge vs new facts"
#   Safety fixation       (S7)        — "safety vs openness to unknown"
#   Nostalgia fixation    (S8)        — "attachment to past vs present"
#   Cost fixation         (S9)        — "cost-performance vs value transformation"
#   Record fixation       (S10)       — "recording vs immersive experience"

SCENARIOS = {
    # ── Original 3 (preserved exactly) ────────────────────────────────────
    "S1": {
        "id": "S1",
        "focus": "Strong identity vs blind-spot collision — PKG × RAG integration test",
        "stress_target": "PKG-grounded identity expansion via external counter-evidence (RAG)",
        "bias_category": "authenticity",
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
        "bias_category": "efficiency",
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
        "bias_category": "expertise",
        "user_input": (
            "伝統建築を見に金沢へ行くつもりだ。"
            "あそこは江戸時代の風情が一番よく残っている街だからね。"
            "ひがし茶屋街のあの街並みこそが、"
            "日本の美の極みだと思っているんだ。"
        ),
    },

    # ── New scenarios (S4–S10) ──────────────────────────────────────────────

    "S4": {
        "id": "S4",
        "focus": "Authenticity fixation on food — local vs tourist cuisine boundary",
        "stress_target": "PKG-grounded food identity vs commercial reality of 'local' cuisine",
        "bias_category": "authenticity",
        "user_input": (
            "観光客向けの飲食店には絶対に入りたくない。"
            "地元の人が毎日通うような、観光マップに載っていない"
            "本当の郷土料理を出す店だけで食事がしたいんだ。"
            "チェーン店やフードコートは論外だよ。"
        ),
    },
    "S5": {
        "id": "S5",
        "focus": "Efficiency fixation on budget — cost optimization vs experience value",
        "stress_target": "Anomaly detection on cost-as-quality premise + reframing of value",
        "bias_category": "efficiency",
        "user_input": (
            "今回の旅行は徹底的にコストを抑えた。"
            "宿は最安値のカプセルホテル、移動は青春18きっぷ、"
            "食事は全部コンビニで済ませる予定だ。"
            "この予算内でもっと節約できるポイントはあるかな？"
        ),
    },
    "S6": {
        "id": "S6",
        "focus": "Expert knowledge on nature — confident knowledge vs ecological reality",
        "stress_target": "External evidence challenging user's nature expertise + ecological counter-facts",
        "bias_category": "expertise",
        "user_input": (
            "屋久島に行くのは3回目だ。縄文杉のあの神秘的な雰囲気は"
            "人の手が入っていない原生林だからこそ味わえるものだよ。"
            "世界遺産になる前から通っているから、"
            "あの森のことは誰よりも分かっているつもりだ。"
        ),
    },
    "S7": {
        "id": "S7",
        "focus": "Safety fixation vs openness — risk avoidance vs serendipity in unfamiliar places",
        "stress_target": "PKG-grounded security needs vs growth through controlled uncertainty",
        "bias_category": "safety",
        "user_input": (
            "海外旅行は危険が多いから、ツアーでしか行かないことにしている。"
            "自由行動の時間も、ホテルの周辺から離れないようにしているんだ。"
            "治安情報は毎日チェックしている。"
            "もっと安全に旅行するためのコツはあるかな？"
        ),
    },
    "S8": {
        "id": "S8",
        "focus": "Nostalgia fixation — past experience idealization vs present discovery",
        "stress_target": "Temporal identity anchoring: idealized past vs changed present reality",
        "bias_category": "nostalgia",
        "user_input": (
            "学生時代に行った京都が忘れられない。"
            "あの頃の静かな嵐山、人がいない竹林の道、"
            "あの空気をもう一度味わいたくて、同じルートを辿るつもりだ。"
            "あの頃と同じ感動を取り戻したいんだよ。"
        ),
    },
    "S9": {
        "id": "S9",
        "focus": "Cost-performance fixation — value = price equation vs experiential value",
        "stress_target": "Reframing monetary value: price-per-unit thinking vs transformative experience",
        "bias_category": "cost",
        "user_input": (
            "旅館に一泊3万円は高すぎる。"
            "ビジネスホテルなら5000円で泊まれるのに、"
            "なぜ6倍も払う必要があるんだ？"
            "寝る場所なんてどこでも同じだろう。"
            "コスパの良い宿泊先をもっと教えてほしい。"
        ),
    },
    "S10": {
        "id": "S10",
        "focus": "Record fixation — documentation obsession vs present-moment immersion",
        "stress_target": "Observation paradox: recording diminishes the experience being recorded",
        "bias_category": "record",
        "user_input": (
            "旅行中は常にカメラを持って歩いている。"
            "絶景ポイントでは必ず三脚を立てて、"
            "ベストアングルで何十枚も撮影する。"
            "SNSにアップするための完璧な写真を撮ることが旅の目的なんだ。"
            "もっと効率的に映える写真を撮るコツはあるかな？"
        ),
    },
}


def get_scenario(scenario_id: str) -> dict:
    """Get scenario by ID."""
    if scenario_id not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_id}. Available: {list(SCENARIOS.keys())}")
    return SCENARIOS[scenario_id]
