"""
ARIA — LangGraph 1.0 Graph Assembly & Compilation
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.agent_config.state import ARIAState
from agent.agent_config.nodes import (
    domain_identifier,
    human_checkpoint,
    data_extractor,
    data_operator,
    rag_retriever,
    data_consolidator,
    triz_analyzer,
    report_generator,
    error_handler,
)
from agent.agent_config.edges import (
    route_after_domain,
    route_after_extraction,
    route_after_operations,
    route_after_triz,
    route_after_error,
)


# ──────────────────────────────────────────────────────────────
# Sub-agent stubs — branchés mais non implémentés
# ──────────────────────────────────────────────────────────────

def research_agent(state: ARIAState) -> dict:
    """STUB — agent de recherche documentaire (non implémenté)."""
    return {
        "needs_research_agent": False,
        "current_node": "research_agent",
    }


def tool_builder_agent(state: ARIAState) -> dict:
    """STUB — agent de création d'outils (non implémenté)."""
    return {
        "needs_tool_builder": False,
        "current_node": "tool_builder_agent",
    }


# ──────────────────────────────────────────────────────────────
# Graph builder
# ──────────────────────────────────────────────────────────────

def build_graph(checkpointer=None) -> StateGraph:
    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = StateGraph(ARIAState)

    # ── Nodes ─────────────────────────────────────────────────
    graph.add_node("domain_identifier",  domain_identifier)
    graph.add_node("human_checkpoint",   human_checkpoint)
    graph.add_node("research_agent",     research_agent)
    graph.add_node("data_extractor",     data_extractor)
    graph.add_node("data_operator",      data_operator)
    graph.add_node("tool_builder_agent", tool_builder_agent)
    graph.add_node("rag_retriever",      rag_retriever)
    graph.add_node("data_consolidator",  data_consolidator)
    graph.add_node("triz_analyzer",      triz_analyzer)
    graph.add_node("report_generator",   report_generator)
    graph.add_node("error_handler",      error_handler)

    # ── Entry ─────────────────────────────────────────────────
    graph.add_edge(START, "domain_identifier")

    # ── Conditional edges ─────────────────────────────────────
    graph.add_conditional_edges(
        "domain_identifier",
        route_after_domain,
        {
            "research_agent":   "research_agent",
            "human_checkpoint": "human_checkpoint",
            "data_extractor":   "data_extractor",
        },
    )

    # stubs → reprennent le flux normal
    graph.add_edge("research_agent",     "data_extractor")
    graph.add_edge("human_checkpoint",   "data_extractor")
    graph.add_edge("tool_builder_agent", "rag_retriever")

    graph.add_conditional_edges(
        "data_extractor",
        route_after_extraction,
        {
            "error_handler": "error_handler",
            "data_operator": "data_operator",
        },
    )

    graph.add_conditional_edges(
        "data_operator",
        route_after_operations,
        {
            "tool_builder_agent": "tool_builder_agent",
            "error_handler":      "error_handler",
            "rag_retriever":      "rag_retriever",
        },
    )

    graph.add_edge("rag_retriever",     "data_consolidator")
    graph.add_edge("data_consolidator", "triz_analyzer")

    graph.add_conditional_edges(
        "triz_analyzer",
        route_after_triz,
        {
            "data_extractor":   "data_extractor",
            "report_generator": "report_generator",
        },
    )

    graph.add_conditional_edges(
        "error_handler",
        route_after_error,
        {
            "data_extractor":   "data_extractor",
            "report_generator": "report_generator",
        },
    )

    graph.add_edge("report_generator", END)

    # ── Compile ───────────────────────────────────────────────
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_checkpoint"],
    )


# ──────────────────────────────────────────────────────────────
# Instance prête à l'emploi
# ──────────────────────────────────────────────────────────────

aria_graph = build_graph()


# ──────────────────────────────────────────────────────────────
# run_aria — point d'entrée principal
# ──────────────────────────────────────────────────────────────

def run_aria(
    data_sources:   list[dict],
    output_formats: list[str] | None = None,
    thread_id:      str = "aria-default",
    stream:         bool = False,
):
    if output_formats is None:
        output_formats = ["json", "markdown", "html", "pdf", "pptx"]

    initial_state: ARIAState = {
        "messages":       [],
        "data_sources":   data_sources,
        "output_formats": output_formats,
        "iteration":      0,
        "errors":         [],
        "node_history":   [],
        "decisions":      [],
        "status":         "running",
        "current_node":   "START",
        "degraded_report": False,
        "needs_research_agent": False,
        "needs_tool_builder":   False,
    }

    config = {"configurable": {"thread_id": thread_id}}

    if stream:
        return aria_graph.stream(initial_state, config=config, stream_mode="updates")

    return aria_graph.invoke(initial_state, config=config)