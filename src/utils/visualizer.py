"""Workflow visualization utilities"""
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WorkflowVisualizer:
    """Visualizer for LangGraph workflow"""
    
    def __init__(self, output_dir: str = "."):
        """
        Initialize visualizer
        
        Args:
            output_dir: Directory to save visualization files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_workflow_diagram(self, workflow, format: str = "mermaid") -> Optional[Path]:
        """
        Save workflow diagram
        
        Args:
            workflow: LangGraph compiled workflow
            format: Output format ('mermaid', 'png', or 'ascii')
            
        Returns:
            Path to saved file or None if failed
        """
        try:
            if format == "mermaid":
                return self._save_mermaid(workflow)
            elif format == "png":
                return self._save_png(workflow)
            elif format == "ascii":
                return self._save_ascii(workflow)
            else:
                logger.error(f"Unsupported format: {format}")
                return None
        except Exception as e:
            logger.error(f"Failed to save workflow diagram: {e}")
            return None
    
    def _save_mermaid(self, workflow) -> Path:
        """Save Mermaid diagram"""
        output_path = self.output_dir / "workflow_diagram.mermaid"
        
        try:
            # Get Mermaid diagram from LangGraph
            graph = workflow.get_graph()
            mermaid_code = graph.draw_mermaid()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(mermaid_code)
            
            # Also create an HTML file for easy viewing
            html_path = self.output_dir / "workflow_diagram.html"
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Multi-Agent Workflow Diagram</title>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true }});
    </script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .mermaid {{
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Multi-Agent System Workflow</h1>
        <p>This diagram shows the flow of the multi-agent system using LangGraph.</p>
        <div class="mermaid">
{mermaid_code}
        </div>
    </div>
</body>
</html>"""
            
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"\n📊 Workflow diagrams saved:")
            print(f"   Mermaid: {output_path}")
            print(f"   HTML: {html_path}")
            print(f"\n   Open {html_path} in your browser to view the diagram!")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate Mermaid diagram: {e}")
            # Create a fallback manual diagram
            return self._create_manual_diagram()
    
    def _save_png(self, workflow) -> Optional[Path]:
        """Save PNG diagram"""
        output_path = self.output_dir / "workflow_diagram.png"
        
        try:
            # Try to use LangGraph's built-in PNG generation
            graph = workflow.get_graph()
            png_data = graph.draw_mermaid_png()
            
            with open(output_path, 'wb') as f:
                f.write(png_data)
            
            print(f"\n📊 Workflow diagram saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.warning(f"PNG generation not available: {e}")
            print("\n⚠️  PNG generation requires additional dependencies.")
            print("   Falling back to Mermaid format...")
            return self._save_mermaid(workflow)
    
    def _save_ascii(self, workflow) -> Path:
        """Save ASCII diagram"""
        output_path = self.output_dir / "workflow_diagram.txt"
        
        try:
            graph = workflow.get_graph()
            ascii_diagram = graph.draw_ascii()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(ascii_diagram)
            
            print(f"\n📊 Workflow diagram saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate ASCII diagram: {e}")
            return self._create_manual_diagram()
    
    def _create_manual_diagram(self) -> Path:
        """Create manual workflow diagram as fallback"""
        output_path = self.output_dir / "workflow_diagram.txt"
        
        diagram = """
╔══════════════════════════════════════════════════════════════════════╗
║           Multi-Agent System Workflow Diagram                         ║
╚══════════════════════════════════════════════════════════════════════╝

                           ┌─────────────────┐
                           │   User Input    │
                           └────────┬────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   1. Perception Agent          │
                    │   - Create Knowledge Graph     │
                    │   - Extract Entities           │
                    │   - Identify User Intent       │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   2. Chair Agent (Set Agenda) │
                    │   - Decompose User Input       │
                    │   - Set Discussion Agenda      │
                    │   - Determine Direction        │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   3. Explorer Agent            │
                    │   - Search External Info       │
                    │   - Find Related Events        │
                    │   - Evaluate Relevance         │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   4. Witness Agent             │
                    │   - Generate Hypotheses        │
                    │   - Abstract Findings          │
                    │   - Create Insights            │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   5. Critic Agent              │
                    │   - Validate Hypotheses        │
                    │   - Check Alignment            │
                    │   - Approve/Reject             │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   6. Chair Agent (Prioritize) │
                    │   - Prioritize Hypotheses      │
                    │   - Based on User Attributes   │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   7. Nudge Agent               │
                    │   - Generate Personalized      │
                    │   - Apply Nudge Techniques     │
                    │   - Create Final Output        │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │   Save to Neo4j Database       │
                    │   - Conversation History       │
                    │   - Knowledge Graph            │
                    │   - User Attributes            │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                           ┌─────────────────┐
                           │  User Output    │
                           └─────────────────┘

════════════════════════════════════════════════════════════════════════

Agent Flow Summary:
1. Perception  → Extract and structure user input
2. Chair (1)   → Set agenda and direction
3. Explorer    → Find external information
4. Witness     → Generate hypotheses
5. Critic      → Validate hypotheses
6. Chair (2)   → Prioritize by user attributes
7. Nudge       → Create personalized output

════════════════════════════════════════════════════════════════════════
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(diagram)
        
        print(f"\n📊 Workflow diagram saved: {output_path}")
        return output_path


# Global visualizer instance
workflow_visualizer = WorkflowVisualizer()
