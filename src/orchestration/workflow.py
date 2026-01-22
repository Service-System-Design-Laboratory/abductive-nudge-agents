"""Multi-Agent Workflow Orchestration using LangGraph"""
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
import logging
import time

from ..agents import (
    ContextAgent,
    ChairAgent,
    ExplorerAgent,
    AbstractAgent,
    CriticAgent,
    DialogAgent
)
from ..models.schemas import AgentState, Message
from ..utils.neo4j_client import neo4j_db
from ..utils.logger import conversation_logger

logger = logging.getLogger(__name__)


class WorkflowState(TypedDict):
    """Workflow state type definition"""
    user_id: str
    conversation_id: str
    user_input: str
    user_attributes: Any
    context_output: Any
    chair_output: Any
    explorer_output: Any
    abstract_output: Any
    critic_output: Any
    dialog_output: Any
    messages: list


class MultiAgentOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph
    
    Workflow:
    1. Context: Create knowledge graph from user input
    2. Chair (1st): Set agenda and discussion direction
    3. Explorer: Search external information
    4. Abstract: Create hypotheses from findings
    5. Critic: Validate hypotheses against agenda
    6. Chair (2nd): Prioritize validated hypotheses
    7. Dialog: Create personalized output
    """
    
    def __init__(self):
        """Initialize orchestrator with all agents"""
        self.context_agent = ContextAgent()
        self.chair_agent = ChairAgent()
        self.explorer_agent = ExplorerAgent()
        self.abstract_agent = AbstractAgent()
        self.critic_agent = CriticAgent()
        self.dialog_agent = DialogAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        # Create state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agents)
        workflow.add_node("context", self._context_node)
        workflow.add_node("chair_set_agenda", self._chair_set_agenda_node)
        workflow.add_node("explorer", self._explorer_node)
        workflow.add_node("abstract", self._abstract_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("chair_prioritize", self._chair_prioritize_node)
        workflow.add_node("dialog", self._dialog_node)
        workflow.add_node("save_to_neo4j", self._save_to_neo4j_node)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("context")
        workflow.add_edge("context", "chair_set_agenda")
        workflow.add_edge("chair_set_agenda", "explorer")
        workflow.add_edge("explorer", "abstract")
        workflow.add_edge("abstract", "critic")
        workflow.add_edge("critic", "chair_prioritize")
        workflow.add_edge("chair_prioritize", "dialog")
        workflow.add_edge("dialog", "save_to_neo4j")
        workflow.add_edge("save_to_neo4j", END)
        
        # Compile workflow
        return workflow.compile()
    
    def _context_node(self, state: WorkflowState) -> WorkflowState:
        """Context agent node"""
        logger.info(">>> Executing Context Agent")
        start_time = time.time()
        
        result = self.context_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Context Agent",
            input_data={"user_input": state.get("user_input")},
            output_data=result.get("context_output"),
            execution_time=execution_time
        )
        
        return result
    
    def _chair_set_agenda_node(self, state: WorkflowState) -> WorkflowState:
        """Chair agent node (1st call - set agenda)"""
        logger.info(">>> Executing Chair Agent (Set Agenda)")
        start_time = time.time()
        
        result = self.chair_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Chair Agent (Set Agenda)",
            input_data={"context_output": state.get("context_output")},
            output_data=result.get("chair_output"),
            execution_time=execution_time
        )
        
        return result
    
    def _explorer_node(self, state: WorkflowState) -> WorkflowState:
        """Explorer agent node"""
        logger.info(">>> Executing Explorer Agent")
        start_time = time.time()
        
        result = self.explorer_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Explorer Agent",
            input_data={"chair_output": state.get("chair_output")},
            output_data=result.get("explorer_output"),
            execution_time=execution_time
        )
        
        return result
    
    def _abstract_node(self, state: WorkflowState) -> WorkflowState:
        """Abstract agent node"""
        logger.info(">>> Executing Abstract Agent")
        start_time = time.time()
        
        result = self.abstract_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Abstract Agent",
            input_data={"explorer_output": state.get("explorer_output")},
            output_data=result.get("abstract_output"),
            execution_time=execution_time
        )
        
        return result
    
    def _critic_node(self, state: WorkflowState) -> WorkflowState:
        """Critic agent node"""
        logger.info(">>> Executing Critic Agent")
        start_time = time.time()
        
        result = self.critic_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Critic Agent",
            input_data={"abstract_output": state.get("abstract_output")},
            output_data=result.get("critic_output"),
            execution_time=execution_time
        )
        
        return result
    
    def _chair_prioritize_node(self, state: WorkflowState) -> WorkflowState:
        """Chair agent node (2nd call - prioritize)"""
        logger.info(">>> Executing Chair Agent (Prioritize)")
        start_time = time.time()
        
        result = self.chair_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Chair Agent (Prioritize)",
            input_data={"critic_output": state.get("critic_output")},
            output_data=result.get("chair_output"),
            execution_time=execution_time
        )
        
        return result
    
    def _dialog_node(self, state: WorkflowState) -> WorkflowState:
        """Dialog agent node"""
        logger.info(">>> Executing Dialog Agent")
        start_time = time.time()
        
        result = self.dialog_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Dialog Agent",
            input_data={"chair_output": state.get("chair_output"), "critic_output": state.get("critic_output")},
            output_data=result.get("dialog_output"),
            execution_time=execution_time
        )
        
        return result
    
    def _save_to_neo4j_node(self, state: WorkflowState) -> WorkflowState:
        """Save results to Neo4j"""
        logger.info(">>> Saving to Neo4j")
        
        try:
            # Save user message
            neo4j_db.add_message(
                conversation_id=state["conversation_id"],
                role="user",
                content=state["user_input"]
            )
            
            # Save assistant message
            if state.get("dialog_output"):
                neo4j_db.add_message(
                    conversation_id=state["conversation_id"],
                    role="assistant",
                    content=state["dialog_output"].nudge_message,
                    agent_name="dialog",
                    metadata={
                        "nudge_type": state["dialog_output"].nudge_type,
                        "personalization_factors": state["dialog_output"].personalization_factors
                    }
                )
            
            # Save knowledge graph from context
            if state.get("context_output"):
                context_data = state["context_output"]
                neo4j_db.create_knowledge_graph(
                    conversation_id=state["conversation_id"],
                    entities=[e.dict() for e in context_data.entities],
                    relationships=[r.dict() for r in context_data.relationships]
                )
            
            logger.info("Successfully saved to Neo4j")
            
        except Exception as e:
            logger.error(f"Error saving to Neo4j: {e}")
        
        return state
    
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the multi-agent workflow
        
        Args:
            state: Initial state with user_id, conversation_id, user_input, etc.
            
        Returns:
            Final state after all agents have processed
        """
        logger.info(f"Starting multi-agent workflow for conversation {state.get('conversation_id')}")
        
        try:
            # Execute workflow
            final_state = self.workflow.invoke(state)
            logger.info("Workflow completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Error in workflow execution: {e}")
            raise
