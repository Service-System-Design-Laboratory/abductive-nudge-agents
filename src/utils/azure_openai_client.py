"""Azure OpenAI client wrapper"""
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
import logging

from ..utils.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Wrapper for Azure OpenAI API"""
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint.split("/openai/deployments")[0]
        )
        self.deployment = settings.azure_openai_deployment
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """Generate chat completion"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    def chat_completion_with_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate chat completion with JSON response format"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error in JSON chat completion: {e}")
            raise


# Global Azure OpenAI client instance
azure_openai_client = AzureOpenAIClient()
