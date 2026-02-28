"""
Tool Builder — LangGraph 1.0 Graph Assembly
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from agent.sub_agents.tool_builder.state import ToolBuilderState
from agent.sub_agents.tool_builder.nodes import (
    code_generator,
    code_tester,
    code_fixer,
    tool_persister,
)
from agent.sub_agents.tool_builder.edges import (
    route_after_test,
    route_after_fix,
)


def build_tool_builder_graph(checkpointer=None):
    if checkpointer is None:
        checkpointer = MemorySaver()

    graph = StateGraph(ToolBuilderState)

    graph.add_node("code_generator",  code_generator)
    graph.add_node("code_tester",     code_tester)
    graph.add_node("code_fixer",      code_fixer)
    graph.add_node("tool_persister",  tool_persister)

    graph.add_edge(START,            "code_generator")
    graph.add_edge("code_generator", "code_tester")

    graph.add_conditional_edges(
        "code_tester",
        route_after_test,
        {
            "tool_persister": "tool_persister",
            "code_fixer":     "code_fixer",
            "END":            END,
        },
    )

    graph.add_conditional_edges(
        "code_fixer",
        route_after_fix,
        {"code_tester": "code_tester"},
    )

    graph.add_edge("tool_persister", END)

    return graph.compile(checkpointer=checkpointer)


tool_builder_graph = build_tool_builder_graph()


def run_tool_builder(tool_spec: dict, thread_id: str = "tool-builder-default") -> dict:
    """
    Point d'entrée — appelé par ARIA quand un outil manque.

    Args:
        tool_spec : {tool_name, description, input_schema, output_schema, example_usage}
        thread_id : ID de thread pour le checkpointer

    Returns:
        ToolResult dict {tool_name, status, code, persisted_at, validated, error}
    """
    initial_state: ToolBuilderState = {
        "messages":      [],
        "tool_spec":     tool_spec,
        "fix_iteration": 0,
        "errors":        [],
        "status":        "running",
        "current_node":  "START",
        "test_passed":   False,
    }

    config = {"configurable": {"thread_id": thread_id}}
    result = tool_builder_graph.invoke(initial_state, config=config)
    return result.get("tool_result", {
        "tool_name": tool_spec.get("tool_name"),
        "status":    "failed",
        "error":     "No result returned from tool builder graph",
    })