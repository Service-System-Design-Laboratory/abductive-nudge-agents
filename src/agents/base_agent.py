"""Base Agent class for all AI agents"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
import time

from ..utils.azure_openai_client import azure_openai_client
from ..utils.logger import conversation_logger

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, name: str, role: str, temperature: float = 0.7):
        """
        Initialize base agent
        
        Args:
            name: Agent name
            role: Agent role description
            temperature: LLM temperature parameter
        """
        self.name = name
        self.role = role
        self.temperature = temperature
        self.client = azure_openai_client
    
    @abstractmethod
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the agent's task
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state
        """
        pass
    
    def _create_system_message(self) -> str:
        """Create system message for the agent"""
        return f"あなたは{self.name}です。{self.role}"
    
    def _call_llm(self, messages: list, use_json: bool = False) -> str:
        """
        Call Azure OpenAI LLM
        
        Args:
            messages: List of messages
            use_json: Whether to use JSON response format
            
        Returns:
            LLM response
        """
        try:
            start_time = time.time()
            
            if use_json:
                response = self.client.chat_completion_with_json(
                    messages=messages,
                    temperature=self.temperature
                )
            else:
                response = self.client.chat_completion(
                    messages=messages,
                    temperature=self.temperature
                )
            
            execution_time = time.time() - start_time
            
            # Log LLM call
            prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            conversation_logger.log_llm_call(
                agent_name=self.name,
                prompt=prompt,
                response=response,
                model=self.client.deployment,
                tokens_used=None  # Azure OpenAI doesn't easily expose token count in response
            )
            
            logger.info(f"[{self.name}] LLM call completed in {execution_time:.2f}s")
            
            return response
            
        except Exception as e:
            logger.error(f"Error calling LLM for {self.name}: {e}")
            raise
    
    def log_action(self, action: str, details: Any = None):
        """Log agent action"""
        log_message = f"[{self.name}] {action}"
        if details:
            log_message += f": {details}"
        logger.info(log_message)
