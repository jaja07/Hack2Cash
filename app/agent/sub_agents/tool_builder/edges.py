"""
Tool Builder — Conditional Edge Routing (LangGraph 1.0)
"""

from __future__ import annotations
from agent.sub_agents.tool_builder.state import ToolBuilderState


def route_after_test(state: ToolBuilderState) -> str:
    """
    - test passé                    → tool_persister
    - test échoué + fix_iteration < 3 → code_fixer
    - test échoué + max retries     → END (échec déclaré)
    """
    if state.get("test_passed", False):
        return "tool_persister"
    if state.get("fix_iteration", 0) < 3:
        return "code_fixer"
    return "END"


def route_after_fix(state: ToolBuilderState) -> str:
    """Après correction → toujours retester."""
    return "code_tester"