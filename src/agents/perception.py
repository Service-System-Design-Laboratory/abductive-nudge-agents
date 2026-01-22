"""Perception Agent - Creates knowledge graph from user input"""
import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.schemas import PerceptionOutput, KnowledgeGraphEntity, KnowledgeGraphRelationship


class PerceptionAgent(BaseAgent):
    """
    Perception Agent
    - Receives user input
    - Creates knowledge graph (entities and relationships)
    - Extracts user intent and key topics
    """
    
    def __init__(self):
        super().__init__(
            name="Perception Agent",
            role="""ユーザーの入力を受け取り、以下の処理を行います:
1. ユーザーの発言から重要なエンティティ(人物、場所、概念など)を抽出
2. エンティティ間の関係性を特定
3. ユーザーの意図を理解
4. 主要なトピックを抽出
5. これらの情報からナレッジグラフを構築

JSON形式で以下の構造で出力してください:
{
    "entities": [{"name": "エンティティ名", "type": "エンティティタイプ", "properties": {}}],
    "relationships": [{"source": "エンティティA", "target": "エンティティB", "type": "関係タイプ", "properties": {}}],
    "user_intent": "ユーザーの意図の説明",
    "key_topics": ["トピック1", "トピック2"]
}""",
            temperature=0.5
        )
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process user input and create knowledge graph"""
        self.log_action("Processing user input", state.get("user_input"))
        
        user_input = state.get("user_input", "")
        conversation_history = state.get("messages", [])
        
        # Create context from conversation history
        history_context = ""
        if conversation_history:
            recent_messages = conversation_history[-5:]  # Last 5 messages
            history_context = "\n".join([
                f"{msg.role}: {msg.content}" 
                for msg in recent_messages
            ])
        
        # Prepare messages for LLM
        messages = [
            {"role": "system", "content": self._create_system_message()},
            {"role": "user", "content": f"""以下のユーザー入力を分析してください。

過去の会話履歴:
{history_context if history_context else "なし"}

現在のユーザー入力:
{user_input}

上記の形式でJSON出力してください。"""}
        ]
        
        # Call LLM
        response = self._call_llm(messages, use_json=True)
        
        # Parse response
        try:
            parsed_response = json.loads(response)
            
            # Create PerceptionOutput
            entities = [
                KnowledgeGraphEntity(**entity) 
                for entity in parsed_response.get("entities", [])
            ]
            
            relationships = [
                KnowledgeGraphRelationship(**rel) 
                for rel in parsed_response.get("relationships", [])
            ]
            
            perception_output = PerceptionOutput(
                entities=entities,
                relationships=relationships,
                user_intent=parsed_response.get("user_intent", ""),
                key_topics=parsed_response.get("key_topics", [])
            )
            
            state["perception_output"] = perception_output
            
            self.log_action("Knowledge graph created", 
                          f"Entities: {len(entities)}, Relationships: {len(relationships)}")
            
        except json.JSONDecodeError as e:
            self.log_action("Error parsing JSON response", str(e))
            raise
        
        return state
