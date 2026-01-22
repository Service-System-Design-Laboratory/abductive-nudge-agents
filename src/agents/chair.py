"""Chair Agent - Decomposes user input and determines discussion agenda"""
import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.schemas import ChairOutput


class ChairAgent(BaseAgent):
    """
    Chair Agent (appears twice in workflow)
    
    First appearance:
    - Decomposes user input
    - Determines overall discussion agenda and direction
    
    Second appearance:
    - Prioritizes validated hypotheses based on user attributes
    """
    
    def __init__(self):
        super().__init__(
            name="Chair Agent",
            role="""会議の議長として、以下の処理を行います:
1. ユーザーの入力を分解して理解
2. 会話の議題を設定
3. 大まかな方向性を決定
4. サブトピックに分解
5. (2回目の呼び出し時) ユーザー属性に基づいて仮説の優先順位を決定

JSON形式で以下の構造で出力してください:
{
    "agenda": "議題の説明",
    "discussion_direction": "会話の方向性",
    "sub_topics": ["サブトピック1", "サブトピック2"],
    "priority_order": ["仮説ID1", "仮説ID2"]  // 2回目の呼び出し時のみ
}""",
            temperature=0.6
        )
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process and determine discussion agenda"""
        perception_output = state.get("perception_output")
        critic_output = state.get("critic_output")
        
        # First call: Set agenda
        if not critic_output:
            return self._set_agenda(state)
        # Second call: Prioritize hypotheses
        else:
            return self._prioritize_hypotheses(state)
    
    def _set_agenda(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """First call: Set discussion agenda"""
        self.log_action("Setting discussion agenda")
        
        perception_output = state.get("perception_output")
        user_input = state.get("user_input", "")
        
        messages = [
            {"role": "system", "content": self._create_system_message()},
            {"role": "user", "content": f"""以下の情報から、会話の議題と方向性を決定してください。

ユーザー入力: {user_input}

ユーザーの意図: {perception_output.user_intent if perception_output else "不明"}

主要トピック: {", ".join(perception_output.key_topics) if perception_output else "なし"}

議題を設定し、会話の方向性を決め、サブトピックに分解してください。
JSON形式で出力してください。"""}
        ]
        
        response = self._call_llm(messages, use_json=True)
        
        try:
            parsed_response = json.loads(response)
            chair_output = ChairOutput(**parsed_response)
            state["chair_output"] = chair_output
            
            self.log_action("Agenda set", chair_output.agenda)
            
        except json.JSONDecodeError as e:
            self.log_action("Error parsing JSON response", str(e))
            raise
        
        return state
    
    def _prioritize_hypotheses(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Second call: Prioritize validated hypotheses"""
        self.log_action("Prioritizing hypotheses based on user attributes")
        
        critic_output = state.get("critic_output")
        user_attributes = state.get("user_attributes")
        chair_output = state.get("chair_output")
        
        validated_hypotheses = critic_output.validated_hypotheses if critic_output else []
        
        messages = [
            {"role": "system", "content": self._create_system_message()},
            {"role": "user", "content": f"""以下の検証済み仮説に対して、ユーザー属性に基づいて優先順位を付けてください。

議題: {chair_output.agenda if chair_output else "未設定"}

ユーザー属性:
{json.dumps(user_attributes.dict() if user_attributes else {}, ensure_ascii=False, indent=2)}

検証済み仮説:
{json.dumps(validated_hypotheses, ensure_ascii=False, indent=2)}

優先順位の高い順にソートし、priority_orderフィールドに仮説のインデックス番号を配列で返してください。
JSON形式で出力してください。"""}
        ]
        
        response = self._call_llm(messages, use_json=True)
        
        try:
            parsed_response = json.loads(response)
            
            # Update chair_output with priority order
            if chair_output:
                chair_output.priority_order = parsed_response.get("priority_order", [])
                state["chair_output"] = chair_output
            
            self.log_action("Hypotheses prioritized", 
                          f"Order: {parsed_response.get('priority_order', [])}")
            
        except json.JSONDecodeError as e:
            self.log_action("Error parsing JSON response", str(e))
            raise
        
        return state
