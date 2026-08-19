"""
schemas/investigator.py — Pydantic schemas for the Agentic Experiment Investigator.
"""

from typing import Any
from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    """A single evidence unit backed by an observable tool result."""

    source_tool: str = Field(description="The exact name of the tool from which this finding was observed")
    finding: str = Field(description="Concrete finding or data point discovered during investigation")


class InvestigationReport(BaseModel):
    """Structured, evidence-backed conclusion produced by the agent."""

    conclusion: str = Field(description="Clear answer to the user's investigation objective")
    evidence: list[EvidenceItem] = Field(default_factory=list, description="List of observed evidence items")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations based on the findings")
    limitations: list[str] = Field(default_factory=list, description="Uncertainties, missing data, or investigation limits")


class InvestigationTraceStep(BaseModel):
    """Observable step in the request-scoped investigation trace."""

    step: int
    tool_name: str
    tool_input: dict[str, Any]
    tool_result: dict[str, Any]


class InvestigateRequest(BaseModel):
    """Payload for POST /api/v1/experiments/{experiment_id}/investigate."""

    objective: str = Field(..., min_length=3, description="Natural-language ML investigation objective")


class InvestigateResponseData(BaseModel):
    """Payload returned inside ApiResponse data field."""

    experiment_id: str
    objective: str
    conclusion: str
    evidence: list[EvidenceItem] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    trace: list[InvestigationTraceStep] = Field(default_factory=list)
    iterations_used: int
    max_iterations: int = 5
