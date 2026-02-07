"""
Pydantic I/O contracts for the Abductive Dialogue Pipeline.
Every agent's input and output is a strict JSON schema.
"""
from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


# ── Shared primitives ──────────────────────────────────────────────

class Observation(BaseModel):
    """A fact extracted directly from user input (cannot be denied)."""
    id: str = Field(..., description="e.g. O1, O2")
    text: str

class Assumption(BaseModel):
    """A tentative premise placed by ContextAgent (revisable)."""
    id: str = Field(..., description="e.g. A1, A2")
    text: str
    status: Literal["tentative", "confirmed", "rejected"] = "tentative"

class Trigger(BaseModel):
    type: Literal["information_gap", "ambiguity", "contradiction", "focus"]
    text: str

class Constraints(BaseModel):
    tone: str = "supportive"
    safety: str = "avoid determinism"


# ── 1. ContextAgent ────────────────────────────────────────────────

class ContextOutput(BaseModel):
    observations: List[Observation] = Field(..., min_length=1)
    assumptions: List[Assumption] = Field(default_factory=list)
    questions: List[str] = Field(..., min_length=1)
    constraints: Constraints = Field(default_factory=Constraints)


# ── 2. ExplorerAgent ───────────────────────────────────────────────

class EvidenceItem(BaseModel):
    rank: int
    title: str
    snippet: str
    url: str
    source_type: Literal["edu", "gov", "org", "com", "other"] = "other"

class ExternalObservation(BaseModel):
    """An observation derived from external search results (world-level fact)."""
    id: str = Field(..., description="e.g. Oext1, Oext2")
    text: str
    source_url: str = Field("", description="URL from which this observation was derived")

class ExplorerOutput(BaseModel):
    triggers: List[Trigger] = Field(default_factory=list)
    rag_queries: List[str] = Field(default_factory=list)
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
    external_observations: List[ExternalObservation] = Field(default_factory=list)
    notes: str = ""


# ── 3. HypothesisAgent ────────────────────────────────────────────

class Hypothesis(BaseModel):
    hypothesis_id: str = Field(..., description="e.g. H1, H2")
    type: str = Field(
        ...,
        description="psychological|environmental|social|skill|value|evidence_gap|goal_mismatch|constraint_conflict|other"
    )
    explains: List[str] = Field(..., description="Which O ids this H explains")
    assumes: List[str] = Field(default_factory=list, description="Which A ids this H relies on")
    statement: str
    mechanism: str
    predictions: List[str] = Field(default_factory=list)
    discriminating_questions: List[str] = Field(default_factory=list)
    persona_link: List[str] = Field(default_factory=list, description="e.g. pkg:node_id")
    evidence_link: List[str] = Field(default_factory=list, description="e.g. ev:1")

class HypothesisOutput(BaseModel):
    hypotheses: List[Hypothesis] = Field(..., min_length=1)


# ── 4. JudgeAgent ─────────────────────────────────────────────────

class JudgeDiagnosis(BaseModel):
    """Diagnostic assessment of a hypothesis (no scores)."""
    fatal_flaws: List[str] = Field(default_factory=list, description="Contradictions, unsupported claims, or unexplained observations")
    explains_confirmed: List[str] = Field(default_factory=list, description="Which O ids are actually explained")
    key_assumptions: List[str] = Field(default_factory=list, description="Critical assumptions this hypothesis depends on")
    best_discriminating_question: str = Field("", description="The single best question to distinguish this hypothesis from others")
    testability_notes: str = Field("", description="How easily this hypothesis can be tested/verified")
    safety_risk_notes: str = Field("", description="Risk of misinterpretation if presented to user")

class Judgement(BaseModel):
    hypothesis_id: str
    diagnosis: JudgeDiagnosis
    rationale: str

class JudgeOutput(BaseModel):
    judgements: List[Judgement] = Field(..., min_length=1)


# ── 5. DecisionAgent ──────────────────────────────────────────────

class UserFacingFrame(BaseModel):
    framing: Literal["options", "question", "reframe"] = "options"
    questions: List[str] = Field(default_factory=list)
    options: List[str] = Field(default_factory=list)

class DecisionOutput(BaseModel):
    selected_hypothesis_id: str
    contrasting_hypothesis_id: str = Field("", description="The hypothesis that offers the most different explanation")
    selection_rationale: str
    user_facing_frame: UserFacingFrame


# ── 6. DialogueAgent ──────────────────────────────────────────────

class EmpathyMarkers(BaseModel):
    acknowledgement: bool = False
    reflection: bool = False
    perspective_prompt: bool = False

class NudgeMarkers(BaseModel):
    # EAST framework
    easy: bool = False              # 認知負荷が低い（明確な選択肢、小さな行動）
    attractive: bool = False        # 個人的に魅力的（PKG由来の関心に結びつく）
    social: bool = False            # 社会的参照（同じ立場の人の例、一般的傾向）
    timely: bool = False            # 今のタイミングで有効な提案
    # Operational sub-markers
    has_question: bool = False
    has_options: bool = False
    has_small_action: bool = False
    directive_level: Literal["low", "mid", "high"] = "low"

class ResponseMarkers(BaseModel):
    empathy: EmpathyMarkers = Field(default_factory=EmpathyMarkers)
    nudge: NudgeMarkers = Field(default_factory=NudgeMarkers)

class DialogueOutput(BaseModel):
    final_response: str
    markers: ResponseMarkers = Field(default_factory=ResponseMarkers)


# ── PKG (Personal Knowledge Graph) ────────────────────────────────

class PKGNode(BaseModel):
    id: str
    label: str
    type: str = Field(..., description="interest|skill|value|experience|concern")
    weight: float = Field(0.5, ge=0.0, le=1.0)

class PKGEdge(BaseModel):
    src: str
    dst: str
    rel: str = "related_to"

class PKGData(BaseModel):
    enabled: bool = True
    nodes: List[PKGNode] = Field(default_factory=list)
    edges: List[PKGEdge] = Field(default_factory=list)

    def to_graph_text(self) -> str:
        """Serialize as node list + edge triples for LLM consumption.
        Preserves the full graph structure (nodes AND relationships)."""
        if not self.enabled or not self.nodes:
            return ""
        node_map = {n.id: n for n in self.nodes}
        lines = ["## ノード一覧"]
        for n in self.nodes:
            lines.append(f"  [{n.id}] {n.label}  (type={n.type}, weight={n.weight})")
        if self.edges:
            lines.append("")
            lines.append("## 関係 (src --[rel]--> dst)")
            for e in self.edges:
                src_label = node_map[e.src].label if e.src in node_map else e.src
                dst_label = node_map[e.dst].label if e.dst in node_map else e.dst
                lines.append(f"  {src_label} --[{e.rel}]--> {dst_label}")
        return "\n".join(lines)


# ── Persona ────────────────────────────────────────────────────────

class Persona(BaseModel):
    persona_id: str
    name: str
    summary: str
    pkg: PKGData = Field(default_factory=PKGData)
