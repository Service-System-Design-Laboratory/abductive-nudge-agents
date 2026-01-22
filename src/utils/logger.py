"""Logging utilities for agent conversations"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


class ConversationLogger:
    """Logger for agent conversations and workflow execution"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize conversation logger
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.conversation_logs: List[Dict[str, Any]] = []
    
    def log_agent_execution(
        self,
        agent_name: str,
        input_data: Any,
        output_data: Any,
        execution_time: float = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Log agent execution details
        
        Args:
            agent_name: Name of the agent
            input_data: Input to the agent
            output_data: Output from the agent
            execution_time: Execution time in seconds
            metadata: Additional metadata
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name,
            "input": self._serialize(input_data),
            "output": self._serialize(output_data),
            "execution_time": execution_time,
            "metadata": metadata or {}
        }
        self.conversation_logs.append(log_entry)
    
    def log_llm_call(
        self,
        agent_name: str,
        prompt: str,
        response: str,
        model: str = None,
        tokens_used: int = None
    ):
        """
        Log LLM API call
        
        Args:
            agent_name: Name of the agent making the call
            prompt: Prompt sent to LLM
            response: Response from LLM
            model: Model name
            tokens_used: Number of tokens used
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "llm_call",
            "agent_name": agent_name,
            "model": model,
            "prompt": prompt,
            "response": response,
            "tokens_used": tokens_used
        }
        self.conversation_logs.append(log_entry)
    
    def save_logs(self, conversation_id: str, user_id: str = None):
        """
        Save logs to files
        
        Args:
            conversation_id: Conversation ID
            user_id: User ID (optional)
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"conversation_{conversation_id}_{timestamp}"
        
        # Save JSON log
        json_path = self.log_dir / f"{base_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "timestamp": timestamp,
                "logs": self.conversation_logs
            }, f, ensure_ascii=False, indent=2)
        
        # Save human-readable text log
        txt_path = self.log_dir / f"{base_filename}.txt"
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"{'='*80}\n")
            f.write(f"Conversation Log\n")
            f.write(f"Conversation ID: {conversation_id}\n")
            if user_id:
                f.write(f"User ID: {user_id}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"{'='*80}\n\n")
            
            for i, log in enumerate(self.conversation_logs, 1):
                f.write(f"\n{'─'*80}\n")
                f.write(f"[{i}] {log.get('agent_name', 'Unknown Agent')}\n")
                f.write(f"Time: {log.get('timestamp', 'N/A')}\n")
                
                if log.get('type') == 'llm_call':
                    f.write(f"\nType: LLM Call\n")
                    f.write(f"Model: {log.get('model', 'N/A')}\n")
                    if log.get('tokens_used'):
                        f.write(f"Tokens Used: {log['tokens_used']}\n")
                    f.write(f"\nPrompt:\n{log.get('prompt', 'N/A')}\n")
                    f.write(f"\nResponse:\n{log.get('response', 'N/A')}\n")
                else:
                    if log.get('execution_time'):
                        f.write(f"Execution Time: {log['execution_time']:.2f}s\n")
                    
                    f.write(f"\nInput:\n")
                    f.write(self._format_data(log.get('input', 'N/A')))
                    f.write(f"\n\nOutput:\n")
                    f.write(self._format_data(log.get('output', 'N/A')))
                    
                    if log.get('metadata'):
                        f.write(f"\n\nMetadata:\n{json.dumps(log['metadata'], ensure_ascii=False, indent=2)}\n")
                
                f.write(f"\n{'─'*80}\n")
        
        print(f"\n📝 Logs saved:")
        print(f"   JSON: {json_path}")
        print(f"   Text: {txt_path}")
        
        return json_path, txt_path
    
    def clear_logs(self):
        """Clear current conversation logs"""
        self.conversation_logs = []
    
    def _serialize(self, data: Any) -> Any:
        """Serialize data for logging"""
        if hasattr(data, 'dict'):
            return data.dict()
        elif hasattr(data, '__dict__'):
            return vars(data)
        elif isinstance(data, (list, tuple)):
            return [self._serialize(item) for item in data]
        elif isinstance(data, dict):
            return {k: self._serialize(v) for k, v in data.items()}
        else:
            return data
    
    def _format_data(self, data: Any, indent: int = 2) -> str:
        """Format data for text output"""
        if isinstance(data, (dict, list)):
            return json.dumps(data, ensure_ascii=False, indent=indent)
        else:
            return str(data)


# Global conversation logger instance
conversation_logger = ConversationLogger()
