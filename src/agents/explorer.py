"""Explorer Agent - Searches for external information"""
import json
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..models.schemas import ExplorerOutput
from ..utils.serper_client import serper_client


class ExplorerAgent(BaseAgent):
    """
    Explorer Agent
    - Searches for external information based on conversation flow
    - Finds multiple related events/facts
    - Returns findings with relevance scores
    """
    
    def __init__(self):
        super().__init__(
            name="Explorer Agent",
            role="""探索者として、以下の処理を行います:
1. 会話の流れから外部情報を調査すべきトピックを特定
2. Serper API (Google検索) を使用して関連する事象、事実、データを複数探索
3. 各発見事項の関連性を評価
4. 情報源を明記

JSON形式で以下の構造で出力してください:
{
    "external_findings": [
        {
            "title": "発見事項のタイトル",
            "description": "詳細説明",
            "context": "議題との関連性",
            "data_points": ["データポイント1", "データポイント2"]
        }
    ],
    "sources": ["情報源1", "情報源2"],
    "relevance_scores": {"finding_0": 0.9, "finding_1": 0.7}
}""",
            temperature=0.7
        )
    
    def _search_external_info(
        self,
        agenda: str,
        sub_topics: List[str],
        key_topics: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search external information using Serper API
        
        Args:
            agenda: Discussion agenda
            sub_topics: Sub-topics from chair
            key_topics: Key topics from perception
            
        Returns:
            List of search results
        """
        # Create search queries from topics
        queries = []
        
        # Main agenda query
        if agenda:
            queries.append(agenda)
        
        # Sub-topic queries
        for topic in sub_topics[:2]:  # Limit to 2 sub-topics
            queries.append(topic)
        
        # Key topic queries
        for topic in key_topics[:2]:  # Limit to 2 key topics
            if topic not in queries:
                queries.append(topic)
        
        # Limit total queries to avoid excessive API calls
        queries = queries[:3]
        
        self.log_action("Searching Serper API", f"Queries: {queries}")
        
        # Search using Serper API
        all_results = []
        for query in queries:
            results = serper_client.search(query, num_results=3)
            all_results.extend(results)
        
        return all_results
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Search for external information"""
        self.log_action("Searching for external information")
        
        chair_output = state.get("chair_output")
        perception_output = state.get("perception_output")
        
        agenda = chair_output.agenda if chair_output else ""
        sub_topics = chair_output.sub_topics if chair_output else []
        key_topics = perception_output.key_topics if perception_output else []
        
        # Search external information using Serper API
        search_results = self._search_external_info(agenda, sub_topics, key_topics)
        
        # Prepare search results context for LLM
        search_context = ""
        if search_results:
            search_context = "\n\n検索結果:\n"
            for i, result in enumerate(search_results[:10], 1):  # Limit to 10 results
                search_context += f"\n{i}. {result.get('title', '')}\n"
                search_context += f"   {result.get('snippet', '')}\n"
                search_context += f"   出典: {result.get('link', '')}\n"
        else:
            search_context = "\n\n(検索結果が取得できませんでした。一般的な知識に基づいて回答してください)"
        
        messages = [
            {"role": "system", "content": self._create_system_message()},
            {"role": "user", "content": f"""以下の議題とトピックに関連する外部情報を探索してください。

議題: {agenda}

サブトピック: {", ".join(sub_topics)}

キートピック: {", ".join(key_topics)}
{search_context}

上記の検索結果を参考に、関連する事象、統計、研究結果、トレンドなどを複数見つけて報告してください。
各発見事項には関連性スコア(0.0-1.0)を付けてください。
情報源(URL)も含めてください。
JSON形式で出力してください。"""}
        ]
        
        response = self._call_llm(messages, use_json=True)
        
        try:
            parsed_response = json.loads(response)
            explorer_output = ExplorerOutput(**parsed_response)
            state["explorer_output"] = explorer_output
            
            self.log_action("External information found", 
                          f"Findings: {len(explorer_output.external_findings)}")
            
        except json.JSONDecodeError as e:
            self.log_action("Error parsing JSON response", str(e))
            raise
        
        return state
