"""
Run configuration and global settings for the Abductive Dialogue Pipeline.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
import os


@dataclass
class ModelConfig:
    name: str = "gpt-4.1"
    temperature: float = 0.2


@dataclass
class RunConfig:
    """Configuration for a single pipeline run."""
    run_id: str = ""
    scenario_id: str = "S1"
    condition: Literal["A", "B", "C", "D"] = "A"

    # Ablation flags
    use_pkg: bool = True
    use_rag: bool = True
    use_judge: bool = True
    is_single: bool = False   # True = single-agent baseline (no pipeline)

    # Generation parameters
    hypothesis_count: int = 5
    rag_top_k: int = 5

    # Model
    model: ModelConfig = field(default_factory=ModelConfig)

    def __post_init__(self):
        if not self.run_id:
            ts = datetime.now().strftime("%Y-%m-%dT%H%M%S")
            if self.is_single:
                self.run_id = f"{ts}__{self.scenario_id}__SINGLE"
            else:
                pkg = "1" if self.use_pkg else "0"
                rag = "1" if self.use_rag else "0"
                judge = "1" if self.use_judge else "0"
                self.run_id = f"{ts}__{self.scenario_id}__PKG{pkg}_RAG{rag}_JUDGE{judge}"

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "condition": self.condition,
            "use_pkg": self.use_pkg,
            "use_rag": self.use_rag,
            "use_judge": self.use_judge,
            "is_single": self.is_single,
            "hypothesis_count": self.hypothesis_count,
            "rag_top_k": self.rag_top_k,
            "model": {"name": self.model.name, "temperature": self.model.temperature},
        }


# ── Ablation condition presets ─────────────────────────────────────

ABLATION_CONDITIONS = {
    "A": {"use_pkg": True,  "use_rag": True,  "use_judge": True,  "is_single": False},  # Full
    "B": {"use_pkg": False, "use_rag": True,  "use_judge": True,  "is_single": False},  # −PKG
    "C": {"use_pkg": True,  "use_rag": False, "use_judge": True,  "is_single": False},  # −RAG
    "D": {"use_pkg": True,  "use_rag": True,  "use_judge": True,  "is_single": True},   # Single Agent (same resources, no decomposition)
}


def make_config(scenario_id: str, condition: str) -> RunConfig:
    """Create a RunConfig from scenario ID and condition letter."""
    flags = ABLATION_CONDITIONS[condition]
    return RunConfig(
        scenario_id=scenario_id,
        condition=condition,
        **flags,
    )


# ── Azure OpenAI settings (from env / .env) ───────────────────────

class AzureSettings:
    """Reads Azure OpenAI credentials from environment."""

    @property
    def api_key(self) -> str:
        return os.environ.get("AZURE_OPENAI_API_KEY", "")

    @property
    def endpoint(self) -> str:
        return os.environ.get("AZURE_OPENAI_ENDPOINT", "")

    @property
    def api_version(self) -> str:
        return os.environ.get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

    @property
    def deployment(self) -> str:
        return os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4.1")


azure_settings = AzureSettings()
