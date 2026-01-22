"""Data models for the multi-agent system"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AgentRole(str, Enum):
    """Agent role enumeration"""
    PERCEPTION = "perception"
    CHAIR = "chair"
    EXPLORER = "explorer"
    WITNESS = "witness"
    CRITIC = "critic"
    NUDGE = "nudge"


class Message(BaseModel):
    """Message model"""
    role: str
    content: str
    agent_name: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UserAttributes(BaseModel):
    """User attributes stored in Neo4j"""
    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    demographics: Dict[str, Any] = Field(default_factory=dict)
    behavior_patterns: Dict[str, Any] = Field(default_factory=dict)
    nudge_receptivity: Dict[str, str] = Field(default_factory=dict)
    

class KnowledgeGraphEntity(BaseModel):
    """Entity in knowledge graph"""
    name: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphRelationship(BaseModel):
    """Relationship in knowledge graph"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)


class PerceptionOutput(BaseModel):
    """Output from Perception Agent"""
    entities: List[KnowledgeGraphEntity]
    relationships: List[KnowledgeGraphRelationship]
    user_intent: str
    key_topics: List[str]


class ChairOutput(BaseModel):
    """Output from Chair Agent"""
    agenda: str
    discussion_direction: str
    sub_topics: List[str]
    priority_order: Optional[List[str]] = None


class ExplorerOutput(BaseModel):
    """Output from Explorer Agent"""
    external_findings: List[Dict[str, Any]]
    sources: List[str]
    relevance_scores: Dict[str, float]


class WitnessOutput(BaseModel):
    """Output from Witness Agent"""
    hypotheses: List[Dict[str, Any]]
    abstractions: List[str]
    confidence_scores: Dict[str, float]


class CriticOutput(BaseModel):
    """Output from Critic Agent"""
    validated_hypotheses: List[Dict[str, Any]]
    rejected_hypotheses: List[Dict[str, Any]]
    alignment_scores: Dict[str, float]
    recommendations: List[str]


class NudgeOutput(BaseModel):
    """Output from Nudge Agent"""
    nudge_message: str
    nudge_type: str
    personalization_factors: List[str]
    expected_impact: str


class AgentState(BaseModel):
    """State passed between agents in the workflow"""
    user_id: str
    conversation_id: str
    user_input: str
    user_attributes: Optional[UserAttributes] = None
    
    # Agent outputs
    perception_output: Optional[PerceptionOutput] = None
    chair_output: Optional[ChairOutput] = None
    explorer_output: Optional[ExplorerOutput] = None
    witness_output: Optional[WitnessOutput] = None
    critic_output: Optional[CriticOutput] = None
    nudge_output: Optional[NudgeOutput] = None
    
    # Conversation history
    messages: List[Message] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True
