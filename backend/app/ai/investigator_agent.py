"""
ai/investigator_agent.py — Agentic loop for the MicroFlow Experiment Investigator.

Coordinates multi-step, dynamic, read-only investigation using Gemini native function calling.
Enforces bounded autonomy (MAX_AGENT_ITERATIONS = 5) and validates structured output.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, TYPE_CHECKING
from sqlalchemy.orm import Session

from app.ai.tools.investigator_tools import (
    dispatch_tool,
    INVESTIGATOR_TOOL_DECLARATIONS,
    ALLOWED_TOOL_NAMES,
)
from app.schemas.investigator import (
    EvidenceItem,
    InvestigationReport,
    InvestigationTraceStep,
)

if TYPE_CHECKING:
    from app.ai.gemini_service import GeminiService
    from app.services.metrics_service import MetricsService
    from app.services.run_result_service import RunResultService
    from app.services.run_service import RunService

logger = logging.getLogger(__name__)

MAX_AGENT_ITERATIONS: int = 5

INVESTIGATOR_SYSTEM_INSTRUCTION = """
You are the MicroFlow Experiment Investigator, an autonomous, evidence-driven ML diagnosis agent.
Your mission is to investigate an ML experiment, its runs, hyperparameters, metrics, and SHAP explainability to fulfill the user's objective.

AVAILABLE READ-ONLY TOOLS:
1. get_experiment_runs(experiment_id): List all runs in the experiment.
2. get_run_config(run_id): Inspect hyperparameters and configurations of a run.
3. get_run_metrics(run_id): Inspect quantitative evaluation metrics (accuracy, precision, recall, f1, roc_auc, time).
4. compare_runs(run_ids): Compare parameters and metrics side-by-side across multiple runs.
5. get_feature_importance(run_id): Inspect SHAP feature importance summary and direction of impact.

INVESTIGATION GUIDELINES:
- Formulate your strategy dynamically based on the objective.
- Always inspect data through tools before making assertions.
- When sufficient evidence is gathered, conclude by outputting a single valid JSON object.
- Never fabricate run IDs, parameter names, metric values, or feature names.
- If data is missing or incomplete, explicitly state it in your conclusion and limitations.

FINAL REPORT FORMAT:
When you have finished investigating, output ONLY a JSON object matching this exact schema (no markdown fences or extra text):
{
  "conclusion": "Clear, concise, evidence-backed conclusion addressing the objective",
  "evidence": [
    {
      "source_tool": "exact_tool_name_used",
      "finding": "Specific observable finding or metric value"
    }
  ],
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2"
  ],
  "limitations": [
    "Known limitation or missing information",
    "Any factors that could not be evaluated"
  ]
}
"""


class InvestigatorAgent:
    def __init__(self, gemini_service: GeminiService) -> None:
        self._gemini = gemini_service

    def run_investigation(
        self,
        experiment_id: str,
        objective: str,
        db: Session,
        run_service: RunService,
        run_result_service: RunResultService,
        metrics_service: MetricsService,
    ) -> tuple[InvestigationReport, list[InvestigationTraceStep], int]:
        """
        Execute the bounded agentic investigation loop for a given experiment and objective.
        Returns (report, trace, iterations_used).
        """
        trace: list[InvestigationTraceStep] = []
        called_tools: set[str] = set()
        iteration = 0

        # Construct initial user prompt
        initial_prompt = (
            f"Experiment ID: {experiment_id}\n"
            f"Investigation Objective: {objective}\n\n"
            f"Begin by inspecting the experiment and its runs using your tools."
        )

        from google.genai import types  # type: ignore

        contents: list[Any] = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=initial_prompt)],
            )
        ]

        function_declarations = [
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t["parameters"],
            )
            for t in INVESTIGATOR_TOOL_DECLARATIONS
        ]
        gemini_tools = [types.Tool(function_declarations=function_declarations)]

        while iteration < MAX_AGENT_ITERATIONS:
            logger.info(
                "InvestigatorAgent iteration %d/%d for experiment %s",
                iteration + 1,
                MAX_AGENT_ITERATIONS,
                experiment_id,
            )

            try:
                response = self._gemini.generate_chat_turn(
                    contents=contents,
                    tools=gemini_tools,
                    system_instruction=INVESTIGATOR_SYSTEM_INSTRUCTION,
                    operation_name=f"investigator_step_{iteration + 1}",
                )
            except Exception as exc:
                logger.exception("Gemini error during investigator turn %d", iteration + 1)
                report = self._construct_fallback_report(
                    objective=objective,
                    trace=trace,
                    error_message=f"Investigation interrupted due to AI service error: {exc}",
                )
                return report, trace, iteration + 1

            # Check for function calls
            function_calls = getattr(response, "function_calls", None)
            
            model_content = None
            if hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, "content") and candidate.content:
                    model_content = candidate.content
                    if not function_calls and hasattr(candidate.content, "parts"):
                        function_calls = [
                            p.function_call for p in candidate.content.parts if hasattr(p, "function_call") and p.function_call
                        ]

            if function_calls:
                # Ensure we append the exact model_content to preserve thought_signature and other internal metadata
                if model_content:
                    contents.append(model_content)
                else:
                    model_parts = []
                    for fc in function_calls:
                        model_parts.append(types.Part.from_function_call(name=fc.name, args=dict(fc.args or {})))
                    contents.append(types.Content(role="model", parts=model_parts))

                response_parts = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args or {})
                    called_tools.add(tool_name)

                    tool_result = dispatch_tool(
                        name=tool_name,
                        arguments=tool_args,
                        db=db,
                        run_service=run_service,
                        run_result_service=run_result_service,
                        metrics_service=metrics_service,
                    )

                    step_num = len(trace) + 1
                    trace.append(
                        InvestigationTraceStep(
                            step=step_num,
                            tool_name=tool_name,
                            tool_input=tool_args,
                            tool_result=tool_result,
                        )
                    )

                    response_parts.append(
                        types.Part.from_function_response(
                            name=tool_name,
                            response=tool_result,
                        )
                    )

                contents.append(types.Content(role="user", parts=response_parts))
                iteration += 1
                continue

            # If no tool calls, model provided text / final report
            raw_text = getattr(response, "text", "") or ""
            parsed_report = self._parse_report_json(raw_text, called_tools)

            if parsed_report:
                return parsed_report, trace, iteration + 1
            else:
                if iteration == 0 and len(trace) == 0:
                    logger.warning("Investigator attempted premature conclusion without calling tools. Reprompting...")
                    contents.append(types.Content(role="model", parts=[types.Part.from_text(text=raw_text)]))
                    contents.append(
                        types.Content(
                            role="user",
                            parts=[
                                types.Part.from_text(
                                    text="You must investigate using the available tools before producing the final JSON report. Please call a tool to gather data."
                                )
                            ],
                        )
                    )
                    iteration += 1
                    continue
                else:
                    report = self._extract_or_synthesize_report(
                        raw_text=raw_text,
                        objective=objective,
                        trace=trace,
                        called_tools=called_tools,
                    )
                    return report, trace, iteration + 1

        logger.warning(
            "InvestigatorAgent reached MAX_AGENT_ITERATIONS (%d) for experiment %s",
            MAX_AGENT_ITERATIONS,
            experiment_id,
        )
        report = self._construct_fallback_report(
            objective=objective,
            trace=trace,
            error_message="Investigation reached the maximum safety limit (5 iterations) before a final conclusion was reached.",
        )
        return report, trace, MAX_AGENT_ITERATIONS

    def _parse_report_json(self, text: str, called_tools: set[str]) -> InvestigationReport | None:
        """Attempt to parse and validate an InvestigationReport from model output."""
        clean = text.strip()
        if clean.startswith("```json"):
            clean = clean[7:]
        if clean.startswith("```"):
            clean = clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()

        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            clean = match.group(0)

        try:
            data = json.loads(clean)
            if not isinstance(data, dict):
                return None

            conclusion = str(data.get("conclusion", "")).strip()
            if not conclusion:
                return None

            raw_evidence = data.get("evidence", [])
            evidence: list[EvidenceItem] = []
            if isinstance(raw_evidence, list):
                for item in raw_evidence:
                    if isinstance(item, dict):
                        src = str(item.get("source_tool", "investigation_trace")).strip()
                        if src not in ALLOWED_TOOL_NAMES and src not in called_tools:
                            src = "observed_tool_data"
                        finding = str(item.get("finding", "")).strip()
                        if finding:
                            evidence.append(EvidenceItem(source_tool=src, finding=finding))

            recommendations = [
                str(r).strip() for r in data.get("recommendations", []) if str(r).strip()
            ]
            limitations = [
                str(l).strip() for l in data.get("limitations", []) if str(l).strip()
            ]

            return InvestigationReport(
                conclusion=conclusion,
                evidence=evidence,
                recommendations=recommendations,
                limitations=limitations,
            )
        except Exception:
            return None

    def _extract_or_synthesize_report(
        self,
        raw_text: str,
        objective: str,
        trace: list[InvestigationTraceStep],
        called_tools: set[str],
    ) -> InvestigationReport:
        """Synthesize a structured report from prose text and trace evidence."""
        evidence: list[EvidenceItem] = []
        for step in trace:
            if step.tool_result.get("success"):
                evidence.append(
                    EvidenceItem(
                        source_tool=step.tool_name,
                        finding=f"Observed data from {step.tool_name} with inputs {step.tool_input}",
                    )
                )

        conclusion = raw_text.strip() if raw_text.strip() else f"Investigation completed for: {objective}"
        return InvestigationReport(
            conclusion=conclusion,
            evidence=evidence,
            recommendations=["Review the observed run parameters and metrics in the trace."],
            limitations=["The model concluded using unstructured output; report synthesized from observed steps."],
        )

    def _construct_fallback_report(
        self,
        objective: str,
        trace: list[InvestigationTraceStep],
        error_message: str,
    ) -> InvestigationReport:
        """Construct a valid partial report when the loop is interrupted or times out."""
        evidence: list[EvidenceItem] = []
        for step in trace:
            if step.tool_result.get("success"):
                evidence.append(
                    EvidenceItem(
                        source_tool=step.tool_name,
                        finding=f"Step {step.step}: Observed result for {step.tool_name}({step.tool_input})",
                    )
                )

        conclusion = (
            f"Investigation partially completed for objective: '{objective}'. "
            f"{len(trace)} investigation step(s) were conducted before halting."
        )

        return InvestigationReport(
            conclusion=conclusion,
            evidence=evidence,
            recommendations=[
                "Inspect the partial investigation trace below for intermediate findings.",
                "Refine the investigation objective or inspect individual runs directly.",
            ],
            limitations=[error_message],
        )
