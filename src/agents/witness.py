"""Witness Agent - Creates hypotheses from explorer findings"""
import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.schemas import WitnessOutput


class WitnessAgent(BaseAgent):
    """
    Witness Agent
    - Takes explorer's external findings
    - Creates hypotheses aligned with agenda and user attributes
    - Abstracts findings into actionable insights
    """
    
    def __init__(self):
        super().__init__(
            name="Witness Agent",
            role="""証人として、以下の処理を行います:
1. Explorerが発見した外部事象を分析
2. 議題とユーザー属性に合わせた仮説を生成
3. 発見事項を抽象化して洞察を導出
4. 各仮説の確信度を評価

JSON形式で以下の構造で出力してください:
{
    "hypotheses": [
        {
            "id": "hypothesis_1",
            "statement": "仮説の内容",
            "supporting_evidence": ["根拠1", "根拠2"],
            "related_findings": [0, 1],  // explorerのfindingsのインデックス
            "user_relevance": "ユーザーとの関連性の説明"
        }
    ],
    "abstractions": ["抽象化された洞察1", "抽象化された洞察2"],
    "confidence_scores": {"hypothesis_1": 0.8, "hypothesis_2": 0.6}
}""",
            temperature=0.6
        )
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create hypotheses from explorer findings"""
        self.log_action("Creating hypotheses from external findings")
        
        explorer_output = state.get("explorer_output")
        chair_output = state.get("chair_output")
        user_attributes = state.get("user_attributes")
        
        if not explorer_output:
            self.log_action("No explorer output found, skipping")
            return state
        
        messages = [
            {"role": "system", "content": self._create_system_message()},
            {"role": "user", "content": f"""以下の情報から仮説を生成してください。

議題: {chair_output.agenda if chair_output else "未設定"}

Explorerの発見事項:
{json.dumps(explorer_output.external_findings, ensure_ascii=False, indent=2)}

ユーザー属性:
{json.dumps(user_attributes.dict() if user_attributes else {}, ensure_ascii=False, indent=2)}

議題とユーザー属性に適合する仮説を複数生成し、それぞれに確信度スコア(0.0-1.0)を付けてください。
また、発見事項を抽象化して一般的な洞察を導き出してください。
JSON形式で出力してください。"""}
        ]
        
        response = self._call_llm(messages, use_json=True)
        
        try:
            parsed_response = json.loads(response)
            witness_output = WitnessOutput(**parsed_response)
            state["witness_output"] = witness_output
            
            self.log_action("Hypotheses created", 
                          f"Count: {len(witness_output.hypotheses)}")
            
        except json.JSONDecodeError as e:
            self.log_action("Error parsing JSON response", str(e))
            raise
        
        return state
