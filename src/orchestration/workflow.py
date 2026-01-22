"""Multi-Agent Workflow Orchestration using LangGraph"""
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END
import logging
import time

from ..agents import (
    PerceptionAgent,
    ChairAgent,
    ExplorerAgent,
    WitnessAgent,
    CriticAgent,
    NudgeAgent
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
    perception_output: Any
    chair_output: Any
    explorer_output: Any
    witness_output: Any
    critic_output: Any
    nudge_output: Any
    messages: list


class MultiAgentOrchestrator:
    """
    Orchestrates the multi-agent workflow using LangGraph
    
    Workflow:
    1. Perception: Create knowledge graph from user input
    2. Chair (1st): Set agenda and discussion direction
    3. Explorer: Search external information
    4. Witness: Create hypotheses from findings
    5. Critic: Validate hypotheses against agenda
    6. Chair (2nd): Prioritize validated hypotheses
    7. Nudge: Create personalized output
    """
    
    def __init__(self):
        """Initialize orchestrator with all agents"""
        self.perception_agent = PerceptionAgent()
        self.chair_agent = ChairAgent()
        self.explorer_agent = ExplorerAgent()
        self.witness_agent = WitnessAgent()
        self.critic_agent = CriticAgent()
        self.nudge_agent = NudgeAgent()
        
        # Build workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        # Create state graph
        workflow = StateGraph(WorkflowState)
        
        # Add nodes (agents)
        workflow.add_node("perception", self._perception_node)
        workflow.add_node("chair_set_agenda", self._chair_set_agenda_node)
        workflow.add_node("explorer", self._explorer_node)
        workflow.add_node("witness", self._witness_node)
        workflow.add_node("critic", self._critic_node)
        workflow.add_node("chair_prioritize", self._chair_prioritize_node)
        workflow.add_node("nudge", self._nudge_node)
        workflow.add_node("save_to_neo4j", self._save_to_neo4j_node)
        
        # Define edges (workflow flow)
        workflow.set_entry_point("perception")
        workflow.add_edge("perception", "chair_set_agenda")
        workflow.add_edge("chair_set_agenda", "explorer")
        workflow.add_edge("explorer", "witness")
        workflow.add_edge("witness", "critic")
        workflow.add_edge("critic", "chair_prioritize")
        workflow.add_edge("chair_prioritize", "nudge")
        workflow.add_edge("nudge", "save_to_neo4j")
        workflow.add_edge("save_to_neo4j", END)
        
        # Compile workflow
        return workflow.compile()
    
    def _perception_node(self, state: WorkflowState) -> WorkflowState:
        """Perception agent node"""
        logger.info(">>> Executing Perception Agent")
        start_time = time.time()
        
        result = self.perception_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Perception Agent",
            input_data={"user_input": state.get("user_input")},
            output_data=result.get("perception_output"),
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
            input_data={"perception_output": state.get("perception_output")},
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
    
    def _witness_node(self, state: WorkflowState) -> WorkflowState:
        """Witness agent node"""
        logger.info(">>> Executing Witness Agent")
        start_time = time.time()
        
        result = self.witness_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Witness Agent",
            input_data={"explorer_output": state.get("explorer_output")},
            output_data=result.get("witness_output"),
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
            input_data={"witness_output": state.get("witness_output")},
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
    
    def _nudge_node(self, state: WorkflowState) -> WorkflowState:
        """Nudge agent node"""
        logger.info(">>> Executing Nudge Agent")
        start_time = time.time()
        
        result = self.nudge_agent.process(state)
        
        execution_time = time.time() - start_time
        conversation_logger.log_agent_execution(
            agent_name="Nudge Agent",
            input_data={"chair_output": state.get("chair_output"), "critic_output": state.get("critic_output")},
            output_data=result.get("nudge_output"),
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
            if state.get("nudge_output"):
                neo4j_db.add_message(
                    conversation_id=state["conversation_id"],
                    role="assistant",
                    content=state["nudge_output"].nudge_message,
                    agent_name="nudge",
                    metadata={
                        "nudge_type": state["nudge_output"].nudge_type,
                        "personalization_factors": state["nudge_output"].personalization_factors
                    }
                )
            
            # Save knowledge graph from perception
            if state.get("perception_output"):
                perception = state["perception_output"]
                neo4j_db.create_knowledge_graph(
                    conversation_id=state["conversation_id"],
                    entities=[e.dict() for e in perception.entities],
                    relationships=[r.dict() for r in perception.relationships]
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
