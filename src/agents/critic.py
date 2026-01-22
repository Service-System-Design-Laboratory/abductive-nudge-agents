"""Critic Agent - Validates hypotheses against agenda"""
import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.schemas import CriticOutput


class CriticAgent(BaseAgent):
    """
    Critic Agent
    - Validates hypotheses from Witness Agent
    - Checks alignment with agenda set by Chair
    - Accepts or rejects hypotheses
    - Provides recommendations
    """
    
    def __init__(self):
        super().__init__(
            name="Critic Agent",
            role="""批評家として、以下の処理を行います:
1. Witnessが提示した仮説を検証
2. Chairが決めた議題との整合性を確認
3. 各仮説を承認または却下
4. 整合性スコアを算出
5. 改善のための推奨事項を提供

JSON形式で以下の構造で出力してください:
{
    "validated_hypotheses": [
        {
            "id": "hypothesis_1",
            "statement": "仮説の内容",
            "validation_status": "approved",
            "alignment_reasoning": "議題との整合性の理由",
            "supporting_evidence": ["根拠1", "根拠2"]
        }
    ],
    "rejected_hypotheses": [
        {
            "id": "hypothesis_2",
            "statement": "仮説の内容",
            "validation_status": "rejected",
            "rejection_reason": "却下の理由"
        }
    ],
    "alignment_scores": {"hypothesis_1": 0.9, "hypothesis_2": 0.3},
    "recommendations": ["推奨事項1", "推奨事項2"]
}""",
            temperature=0.5
        )
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate hypotheses against agenda"""
        self.log_action("Validating hypotheses")
        
        witness_output = state.get("witness_output")
        chair_output = state.get("chair_output")
        
        if not witness_output or not chair_output:
            self.log_action("Missing witness or chair output, skipping")
            return state
        
        messages = [
            {"role": "system", "content": self._create_system_message()},
            {"role": "user", "content": f"""以下の仮説を検証してください。

議題: {chair_output.agenda}
会話の方向性: {chair_output.discussion_direction}
サブトピック: {", ".join(chair_output.sub_topics)}

Witnessの仮説:
{json.dumps(witness_output.hypotheses, ensure_ascii=False, indent=2)}

各仮説について:
1. 議題との整合性を評価(0.0-1.0のスコア)
2. 整合性が高い(0.6以上)場合は承認、低い場合は却下
3. 承認/却下の理由を明記
4. 全体的な改善推奨事項を提供

JSON形式で出力してください。"""}
        ]
        
        response = self._call_llm(messages, use_json=True)
        
        try:
            parsed_response = json.loads(response)
            critic_output = CriticOutput(**parsed_response)
            state["critic_output"] = critic_output
            
            self.log_action("Hypotheses validated", 
                          f"Approved: {len(critic_output.validated_hypotheses)}, "
                          f"Rejected: {len(critic_output.rejected_hypotheses)}")
            
        except json.JSONDecodeError as e:
            self.log_action("Error parsing JSON response", str(e))
            raise
        
        return state
