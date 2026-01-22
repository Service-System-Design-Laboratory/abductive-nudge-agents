"""Main application entry point"""
import logging
import uuid
from typing import Optional

from .orchestration.workflow import MultiAgentOrchestrator
from .utils.neo4j_client import neo4j_db
from .models.schemas import UserAttributes, Message
from .utils.logger import conversation_logger
from .utils.visualizer import workflow_visualizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """Main multi-agent system interface"""
    
    def __init__(self):
        """Initialize the multi-agent system"""
        self.orchestrator = MultiAgentOrchestrator()
        logger.info("Multi-agent system initialized")
        
        # Generate and save workflow diagram
        try:
            workflow_visualizer.save_workflow_diagram(self.orchestrator.workflow, format="mermaid")
        except Exception as e:
            logger.warning(f"Could not generate workflow diagram: {e}")
    
    def create_or_get_user(self, user_id: str, initial_attributes: Optional[dict] = None) -> UserAttributes:
        """
        Create or retrieve user from Neo4j
        
        Args:
            user_id: Unique user identifier
            initial_attributes: Initial user attributes (for new users)
            
        Returns:
            UserAttributes object
        """
        # Check if user exists
        user_data = neo4j_db.get_user_attributes(user_id)
        
        if not user_data:
            # Create new user
            logger.info(f"Creating new user: {user_id}")
            attributes = initial_attributes or {
                "preferences": {},
                "demographics": {},
                "behavior_patterns": {},
                "nudge_receptivity": {}
            }
            neo4j_db.create_user(user_id, attributes)
            user_data = neo4j_db.get_user_attributes(user_id)
        
        return UserAttributes(
            user_id=user_id,
            preferences=user_data.get("preferences", {}),
            demographics=user_data.get("demographics", {}),
            behavior_patterns=user_data.get("behavior_patterns", {}),
            nudge_receptivity=user_data.get("nudge_receptivity", {})
        )
    
    def create_conversation(self, user_id: str, metadata: Optional[dict] = None) -> str:
        """
        Create a new conversation
        
        Args:
            user_id: User identifier
            metadata: Optional conversation metadata
            
        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())
        neo4j_db.create_conversation(conversation_id, user_id, metadata)
        logger.info(f"Created conversation: {conversation_id}")
        return conversation_id
    
    def process_message(
        self,
        user_id: str,
        conversation_id: str,
        user_input: str
    ) -> str:
        """
        Process user message through the multi-agent system
        
        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
            user_input: User's input message
            
        Returns:
            System response
        """
        logger.info(f"Processing message for user {user_id} in conversation {conversation_id}")
        
        # Clear previous logs
        conversation_logger.clear_logs()
        
        # Get user attributes
        user_attributes = self.create_or_get_user(user_id)
        
        # Get conversation history
        history = neo4j_db.get_conversation_history(conversation_id)
        messages = [
            Message(
                role=msg.get("role"),
                content=msg.get("content"),
                agent_name=msg.get("agent_name")
            )
            for msg in history
        ]
        
        # Prepare initial state
        initial_state = {
            "user_id": user_id,
            "conversation_id": conversation_id,
            "user_input": user_input,
            "user_attributes": user_attributes,
            "messages": messages,
            "perception_output": None,
            "chair_output": None,
            "explorer_output": None,
            "witness_output": None,
            "critic_output": None,
            "nudge_output": None
        }
        
        # Run workflow
        final_state = self.orchestrator.run(initial_state)
        
        # Extract response
        response = ""
        if final_state.get("nudge_output"):
            response = final_state["nudge_output"].nudge_message
        else:
            response = "申し訳ございません。処理中にエラーが発生しました。"
        
        # Save conversation logs
        conversation_logger.save_logs(conversation_id, user_id)
        
        logger.info(f"Response generated: {response[:100]}...")
        return response
    
    def update_user_attributes(self, user_id: str, attributes: dict):
        """
        Update user attributes
        
        Args:
            user_id: User identifier
            attributes: Attributes to update
        """
        neo4j_db.update_user_attributes(user_id, attributes)
        logger.info(f"Updated attributes for user {user_id}")
    
    def close(self):
        """Close all connections"""
        neo4j_db.close()
        logger.info("Multi-agent system closed")
