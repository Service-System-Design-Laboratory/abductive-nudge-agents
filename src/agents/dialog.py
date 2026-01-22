"""Dialog Agent - Creates personalized nudges for user output"""
import json
from typing import Dict, Any

from .base_agent import BaseAgent
from ..models.schemas import DialogOutput


class DialogAgent(BaseAgent):
    """
    Dialog Agent
    - Creates personalized nudges based on user attributes
    - Applies behavioral science principles
    - Generates final output to user
    """
    
    def __init__(self):
        super().__init__(
            name="Dialog Agent",
            role="""ナッジの専門家として、以下の処理を行います:
1. ユーザー属性から最適なナッジ手法を選択
2. 優先順位付けされた仮説を基にメッセージを作成
3. ユーザーが受け入れやすい形式で情報を提示
4. 行動変容を促す要素を組み込む

ナッジのタイプ:
- social_proof: 社会的証明(他者の行動を示す)
- loss_aversion: 損失回避(失うものを強調)
- default_option: デフォルト設定(推奨オプションを提示)
- framing: フレーミング(肯定的な表現)
- scarcity: 希少性(限定性を強調)
- commitment: コミットメント(小さな約束から)

JSON形式で以下の構造で出力してください:
{
    "nudge_message": "ユーザーへの最終メッセージ",
    "nudge_type": "使用したナッジタイプ",
    "personalization_factors": ["考慮した個人化要因1", "要因2"],
    "expected_impact": "期待される効果の説明"
}""",
            temperature=0.7
        )
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Create personalized nudge for user"""
        self.log_action("Creating personalized nudge")
        
        chair_output = state.get("chair_output")
        critic_output = state.get("critic_output")
        user_attributes = state.get("user_attributes")
        user_input = state.get("user_input", "")
        
        if not critic_output or not critic_output.validated_hypotheses:
            self.log_action("No validated hypotheses, creating generic response")
            # Create a generic helpful response
            state["dialog_output"] = DialogOutput(
                nudge_message="ご質問ありがとうございます。もう少し詳しく教えていただけますか?",
                nudge_type="clarification",
                personalization_factors=["初回対話"],
                expected_impact="ユーザーの意図をより明確に理解する"
            )
            return state
        
        # Get prioritized hypotheses
        priority_order = chair_output.priority_order if chair_output and chair_output.priority_order else []
        validated_hypotheses = critic_output.validated_hypotheses
        
        # Reorder hypotheses by priority if available
        if priority_order:
            try:
                ordered_hypotheses = [validated_hypotheses[int(i)] for i in priority_order if int(i) < len(validated_hypotheses)]
            except (ValueError, IndexError):
                ordered_hypotheses = validated_hypotheses
        else:
            ordered_hypotheses = validated_hypotheses
        
        messages = [
            {"role": "system", "content": self._create_system_message()},
            {"role": "user", "content": f"""以下の情報を基に、ユーザーへの最適なナッジメッセージを作成してください。

ユーザーの元の質問/入力:
{user_input}

ユーザー属性:
{json.dumps(user_attributes.dict() if user_attributes else {}, ensure_ascii=False, indent=2)}

優先順位付けされた検証済み仮説(上から優先度高):
{json.dumps(ordered_hypotheses, ensure_ascii=False, indent=2)}

Criticの推奨事項:
{json.dumps(critic_output.recommendations, ensure_ascii=False, indent=2)}

ユーザー属性を考慮して最も効果的なナッジタイプを選択し、
自然で親しみやすい日本語でメッセージを作成してください。
メッセージは具体的で実用的なものにしてください。

JSON形式で出力してください。"""}
        ]
        
        response = self._call_llm(messages, use_json=True)
        
        try:
            parsed_response = json.loads(response)
            dialog_output = DialogOutput(**parsed_response)
            state["dialog_output"] = dialog_output
            
            self.log_action("Nudge created", dialog_output.nudge_type)
            
        except json.JSONDecodeError as e:
            self.log_action("Error parsing JSON response", str(e))
            raise
        
        return state
