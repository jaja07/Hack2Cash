"""
ARIA — LangGraph 1.0 Graph Assembly & Compilation
"""

from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
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
    """Appelle le tool_builder via le serveur MCP sub_agents (port 8002)."""
    import asyncio
    import json
    import traceback
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    
    # Import TextContent si disponible, sinon utiliser une approche générique
    try:
        from mcp.types import TextContent
    except ImportError:
        TextContent = None

    spec   = state.get("missing_tool_spec", {})
    errors = list(state.get("errors", []))

    async def _call_mcp():
        try:
            async with streamablehttp_client("http://localhost:8002/mcp") as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # Appel de l'outil MCP
                    result = await session.call_tool("build_tool", arguments={
                        "tool_name":     spec.get("tool_name"),
                        "description":   spec.get("description", ""),
                        "input_schema":  spec.get("input_schema", {}),
                        "output_schema": spec.get("output_schema", {}),
                        "example_usage": spec.get("example_usage", ""),
                    })
                    
                    # Debug: log de la structure de résultat (peut être retiré après validation)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"MCP result type: {type(result)}, has content: {hasattr(result, 'content')}, dir: {[a for a in dir(result) if not a.startswith('_')]}")
                    
                    # Extraire le contenu texte de la réponse MCP
                    # La réponse MCP contient une liste de blocs de contenu
                    if hasattr(result, "content") and result.content:
                        # Parcourir tous les blocs de contenu
                        for block in result.content:
                            # Si c'est un bloc texte (avec TextContent ou type similaire)
                            if TextContent and isinstance(block, TextContent):
                                try:
                                    return json.loads(block.text)
                                except json.JSONDecodeError:
                                    # Si ce n'est pas du JSON, c'est peut-être une erreur du serveur
                                    error_text = block.text[:500] if hasattr(block, "text") else str(block)[:500]
                                    return {
                                        "status": "failed",
                                        "error": f"Invalid JSON in MCP response: {error_text}",
                                        "tool_name": spec.get("tool_name", "unknown"),
                                        "validated": False,
                                    }
                            # Si le bloc a un attribut text directement (approche générique)
                            elif hasattr(block, "text"):
                                try:
                                    text_content = block.text if isinstance(block.text, str) else str(block.text)
                                    # Essayer de parser comme JSON
                                    parsed = json.loads(text_content)
                                    return parsed
                                except json.JSONDecodeError:
                                    # Si ce n'est pas du JSON, vérifier si c'est une erreur du serveur
                                    text_str = str(block.text) if hasattr(block, "text") else str(block)
                                    # Si le texte contient "Error" ou "error", c'est probablement une erreur du serveur
                                    if "error" in text_str.lower() or "Error" in text_str:
                                        return {
                                            "status": "failed",
                                            "error": text_str[:500],  # Limiter la taille
                                            "tool_name": spec.get("tool_name", "unknown"),
                                            "validated": False,
                                        }
                                    # Sinon, essayer d'accéder au dict directement
                                    if isinstance(block, dict):
                                        return block
                                    return {"status": "failed", "error": f"Could not parse block text: {text_str[:200]}"}
                                except (TypeError, AttributeError) as e:
                                    # Essayer d'accéder au dict directement si c'est déjà un dict
                                    if isinstance(block, dict):
                                        return block
                                    return {"status": "failed", "error": f"Could not parse block: {type(block)}, error: {str(e)}"}
                            # Si le bloc est déjà un dict, le retourner directement
                            elif isinstance(block, dict):
                                return block
                    
                    # Si aucun contenu trouvé, essayer d'accéder directement au résultat
                    if hasattr(result, "result"):
                        if isinstance(result.result, dict):
                            return result.result
                        elif isinstance(result.result, str):
                            try:
                                return json.loads(result.result)
                            except json.JSONDecodeError:
                                return {"status": "failed", "error": f"Result is not JSON: {result.result[:200]}"}
                    
                    return {"status": "failed", "error": f"No content in MCP response. Result type: {type(result)}, attributes: {dir(result)}"}
                    
        except asyncio.CancelledError:
            raise
        except Exception as e:
            error_msg = f"MCP call error: {str(e)}\n{traceback.format_exc()}"
            return {"status": "failed", "error": error_msg}

    try:
        result = asyncio.run(_call_mcp())
        if not isinstance(result, dict):
            result = {"status": "failed", "error": f"Unexpected result type: {type(result)}"}
    except Exception as e:
        error_msg = f"tool_builder_agent MCP call failed: {str(e)}\n{traceback.format_exc()}"
        errors.append(error_msg)
        result = {"status": "failed", "error": error_msg}

    # ── Validation par ARIA ───────────────────────────────────
    validated = False
    if result.get("status") == "success" and result.get("code"):
        try:
            namespace: dict = {}
            exec(compile(result["code"], "<aria_validation>", "exec"), namespace)  # noqa: S102
            tool_fn   = namespace.get(spec.get("tool_name"))
            validated = callable(tool_fn)
        except Exception as e:
            errors.append(f"tool_builder_agent validation failed: {str(e)}")

    result["validated"] = validated

    return {
        "needs_tool_builder":  False,
        "missing_tool_spec":   {},
        "tool_builder_result": result,
        "current_node":        "tool_builder_agent",
        "errors":              errors,
    }


# ──────────────────────────────────────────────────────────────
# Graph builder
# ──────────────────────────────────────────────────────────────

def build_graph(checkpointer=None) -> CompiledStateGraph:
    """Assemble et compile le graphe ARIA. Le checkpointer peut être passé en argument pour la persistance d'état."""
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
    user_query:     str | None = None,
):
    if output_formats is None:
        output_formats = ["json", "markdown", "html", "pdf", "pptx"]

    initial_state: ARIAState = {
        "messages":       [],
        "data_sources":   data_sources,
        "output_formats": output_formats,
        "iteration":      0,
        "user_query":     user_query,
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