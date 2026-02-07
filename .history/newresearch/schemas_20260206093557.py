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
    triggers: List[Trigger] = Field(..., min_length=1)
    questions: List[str] = Field(..., min_length=1)
    rag_queries: List[str] = Field(default_factory=list)
    constraints: Constraints = Field(default_factory=Constraints)


# ── 2. ExplorerAgent ───────────────────────────────────────────────

class EvidenceItem(BaseModel):
    rank: int
    title: str
    snippet: str
    url: str
    source_type: Literal["edu", "gov", "org", "com", "other"] = "other"

class ExplorerOutput(BaseModel):
    evidence_items: List[EvidenceItem] = Field(default_factory=list)
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

class JudgeScores(BaseModel):
    explanatory_power: int = Field(..., ge=1, le=5)
    consistency: int = Field(..., ge=1, le=5)
    persona_alignment: int = Field(..., ge=1, le=5)
    evidence_reliability: int = Field(..., ge=1, le=5)

    @property
    def total(self) -> int:
        return (self.explanatory_power + self.consistency
                + self.persona_alignment + self.evidence_reliability)

class Judgement(BaseModel):
    hypothesis_id: str
    scores: JudgeScores
    rationale: str
    fatal_flaws: List[str] = Field(default_factory=list)

class JudgeOutput(BaseModel):
    judgements: List[Judgement] = Field(..., min_length=1)


# ── 5. DecisionAgent ──────────────────────────────────────────────

class UserFacingFrame(BaseModel):
    framing: Literal["options", "question", "reframe"] = "options"
    questions: List[str] = Field(default_factory=list)
    options: List[str] = Field(default_factory=list)

class DecisionOutput(BaseModel):
    selected_hypothesis_id: str
    selection_rationale: str
    user_facing_frame: UserFacingFrame


# ── 6. DialogueAgent ──────────────────────────────────────────────

class EmpathyMarkers(BaseModel):
    acknowledgement: bool = False
    reflection: bool = False
    perspective_prompt: bool = False

class NudgeMarkers(BaseModel):
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

    def summary(self) -> str:
        """Generate a text summary of PKG for prompt injection."""
        if not self.enabled or not self.nodes:
            return ""
        lines = []
        for n in self.nodes:
            lines.append(f"- {n.label} (type={n.type}, weight={n.weight})")
        return "ペルソナ知識グラフ:\n" + "\n".join(lines)


# ── Persona ────────────────────────────────────────────────────────

class Persona(BaseModel):
    persona_id: str
    name: str
    summary: str
    pkg: PKGData = Field(default_factory=PKGData)
