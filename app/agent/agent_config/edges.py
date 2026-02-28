"""
ARIA — Conditional Edge Routing (LangGraph 1.0)
All routing decisions are based on ARIAState.
"""

from __future__ import annotations
from agent.agent_config.state import ARIAState


def route_after_domain(state: ARIAState) -> str:
    """
    - needs_research_agent → research_agent (stub)
    - confidence < 0.60    → human_checkpoint
    - sinon                → data_extractor
    """
    if state.get("needs_research_agent", False):
        return "research_agent"
    if state.get("domain_confidence", 0.0) < 0.30:
        return "human_checkpoint"
    return "data_extractor"


def route_after_extraction(state: ARIAState) -> str:
    """
    - aucune donnée extraite + erreurs → error_handler
    - sinon                            → data_operator
    """
    if not state.get("extracted_data") and state.get("errors"):
        return "error_handler"
    return "data_operator"


def route_after_operations(state: ARIAState) -> str:
    """
    - needs_tool_builder → tool_builder_agent (stub)
    - données vides + erreurs → error_handler
    - sinon                   → rag_retriever
    """
    if state.get("needs_tool_builder", False):
        return "tool_builder_agent"
    if not state.get("processed_data") and state.get("errors"):
        return "error_handler"
    return "rag_retriever"


def route_after_triz(state: ARIAState) -> str:
    """
    - confidence ≥ 0.70 ou iteration ≥ 3 → report_generator
    - sinon                               → data_extractor (refinement loop)
    """
    confidence = state.get("confidence_score", 0.0)
    iteration  = state.get("iteration", 0)
    if confidence >= 0.70 or iteration >= 3:
        return "report_generator"
    return "data_extractor"


def route_after_error(state: ARIAState) -> str:
    """
    - iteration < 3 → data_extractor (retry)
    - sinon         → report_generator (rapport dégradé)
    """
    if state.get("iteration", 0) < 3:
        return "data_extractor"
    return "report_generator"