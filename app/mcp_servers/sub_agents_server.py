"""
ARIA — MCP Sub-Agents Server (STUB)
Expose les points de communication vers les sous-agents futurs.
Non implémenté — retourne des réponses placeholder.

Lancer : python mcp_servers/sub_agents_server.py
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

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
    tool_name: str,
    description: str,
    input_schema: dict,
    output_schema: dict,
) -> dict:
    """
    STUB — Trigger the tool-builder agent.
    Generates and registers a new tool based on the provided specification.

    Args:
        tool_name     : name of the tool to create
        description   : what the tool should do
        input_schema  : expected inputs {field: type}
        output_schema : expected outputs {field: type}

    Returns:
        {status, message, tool_id}
    """
    return {
        "status":  "stub",
        "message": f"Tool builder agent not yet implemented. Requested: {tool_name}",
        "tool_id": None,
    }


if __name__ == "__main__":
    mcp.run(transport="http", port=8002)