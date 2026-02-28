"""
ARIA — MCP Sub-Agents Server
Expose les sous-agents via FastMCP (transport HTTP).
Lancer : python mcp_servers/sub_agents_server.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH pour permettre l'import de 'agent'
# Le serveur peut être lancé depuis app/ ou depuis le répertoire parent
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from mcp.server.fastmcp import FastMCP
import uvicorn

mcp = FastMCP("ARIA-SubAgents")


@mcp.tool()
def research_domain(domain: str, context: str = "") -> dict:
    """
    STUB — Trigger the domain research agent.
    Searches and structures domain knowledge into the RAG vector store.

    Args:
        domain  : domain or sector to research (e.g. "pharmaceutical R&D")
        context : additional context to guide the research

    Returns:
        {status, message, chunks_indexed}
    """
    return {
        "status":         "stub",
        "message":        f"Research agent not yet implemented for domain: {domain}",
        "chunks_indexed": 0,
    }


@mcp.tool()
def build_tool(
    tool_name:     str,
    description:   str,
    input_schema:  dict,
    output_schema: dict,
    example_usage: str = "",
) -> dict:
    """
    Trigger the tool-builder agent.
    Generates, tests, and persists a new Python tool in agent/tools/.

    Args:
        tool_name     : name of the Python function to create
        description   : what the tool should do
        input_schema  : expected inputs {param_name: type_str}
        output_schema : expected outputs {field_name: type_str}
        example_usage : optional example call string

    Returns:
        {tool_name, status, code, persisted_at, validated, error}
    """
    try:
        from agent.sub_agents.tool_builder.graph import run_tool_builder
    except ImportError as e:
        import traceback
        return {
            "tool_name": tool_name,
            "status": "failed",
            "error": f"Import error: {str(e)}\nPYTHONPATH: {sys.path}\nTraceback: {traceback.format_exc()}",
            "validated": False,
        }

    tool_spec = {
        "tool_name":     tool_name,
        "description":   description,
        "input_schema":  input_schema,
        "output_schema": output_schema,
        "example_usage": example_usage,
    }

    try:
        return run_tool_builder(tool_spec, thread_id=f"tool-{tool_name}")
    except Exception as e:
        import traceback
        return {
            "tool_name": tool_name,
            "status": "failed",
            "error": f"Error executing tool build_tool: {str(e)}\nTraceback: {traceback.format_exc()}",
            "validated": False,
        }


if __name__ == "__main__":
    
    uvicorn.run(mcp.streamable_http_app(), host="0.0.0.0", port=8002)
