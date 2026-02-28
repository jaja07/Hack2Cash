"""
ARIA — MCP Tools Server
Expose tous les outils ARIA via FastMCP (transport HTTP).
Lancer : python mcp_servers/tools_server.py
"""

from __future__ import annotations

import importlib
import inspect
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Imports statiques des outils de base
from agent.tools.extract import (
    extract_from_file,
    extract_from_database,
    extract_from_api,
    extract_from_web,
)
from agent.tools.operations import (
    filter_data,
    aggregate_data,
    normalize_data,
    compare_data,
)
from agent.tools.consolidation import consolidate_report
from agent.tools.rag import query_rag

mcp = FastMCP("ARIA-Tools")


def _discover_dynamic_tools():
    """
    Découvre et charge dynamiquement les outils créés par le tool_builder.
    Les outils doivent être dans agent/tools/ et avoir une fonction du même nom que le fichier.
    """
    tools_dir = Path(__file__).parent.parent / "agent" / "tools"
    dynamic_tools = {}
    
    # Liste des outils de base à exclure (déjà chargés statiquement)
    base_tools = {
        "extract", "operations", "consolidation", "rag", 
        "renderers", "visualizations", "__init__", "__pycache__"
    }
    
    # Parcourir les fichiers Python dans tools/
    for tool_file in tools_dir.glob("*.py"):
        tool_name = tool_file.stem
        
        # Ignorer les fichiers de base et les fichiers spéciaux
        if tool_name in base_tools:
            continue
        
        try:
            # Importer dynamiquement le module
            module_name = f"agent.tools.{tool_name}"
            
            # Recharger le module s'il existe déjà (pour prendre en compte les modifications)
            import sys
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            # Chercher une fonction avec le même nom que le fichier
            if hasattr(module, tool_name):
                tool_func = getattr(module, tool_name)
                if callable(tool_func):
                    dynamic_tools[tool_name] = tool_func
        except Exception as e:
            # Ignorer les erreurs d'import (fichiers invalides, etc.)
            print(f"Warning: Could not load tool {tool_name}: {e}")
            continue
    
    return dynamic_tools


# Charger les outils dynamiques au démarrage
_dynamic_tools = _discover_dynamic_tools()


# ──────────────────────────────────────────────────────────────
# Extraction tools
# ──────────────────────────────────────────────────────────────

@mcp.tool()
def tool_extract_from_file(source: dict) -> dict:
    """
    Extract content from a local file.
    Supported formats: pdf, csv, excel, json, txt, md, html.
    source: {source_id, source_type, path_or_url, data_format, metadata}
    """
    return extract_from_file(source)


@mcp.tool()
def tool_extract_from_database(source: dict) -> dict:
    """
    Extract data from a SQLite or SQL database.
    source.metadata must contain 'query' or 'table'.
    """
    return extract_from_database(source)


@mcp.tool()
def tool_extract_from_api(source: dict) -> dict:
    """
    Fetch data from a REST or GraphQL API endpoint.
    source.metadata: {method, headers, params, body, auth}
    """
    return extract_from_api(source)


@mcp.tool()
def tool_extract_from_web(source: dict) -> dict:
    """
    Scrape structured or unstructured content from a public web page.
    source.metadata: {selectors, extract_tables}
    """
    return extract_from_web(source)


# ──────────────────────────────────────────────────────────────
# Operation tools
# ──────────────────────────────────────────────────────────────

@mcp.tool()
def tool_filter_data(
    records: list,
    conditions: dict | None = None,
    date_field: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    fields: list | None = None,
) -> list:
    """
    Filter a list of records by conditions, date range, or field projection.
    """
    return filter_data(
        records,
        conditions=conditions,
        date_field=date_field,
        date_from=date_from,
        date_to=date_to,
        fields=fields,
    )


@mcp.tool()
def tool_aggregate_data(
    records: list,
    group_by: str | None = None,
    metrics: list | None = None,
    top_n: int | None = None,
    sort_by: str | None = None,
    sort_order: str = "desc",
) -> list:
    """
    Group and aggregate records. metrics: [{field, op}] where op in sum|avg|count|min|max.
    """
    return aggregate_data(
        records,
        group_by=group_by,
        metrics=metrics,
        top_n=top_n,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@mcp.tool()
def tool_normalize_data(
    records: list,
    method: str = "minmax",
    numeric_fields: list | None = None,
    date_format: str | None = None,
    rename_map: dict | None = None,
) -> list:
    """
    Normalize records. method: minmax | zscore | none.
    """
    return normalize_data(
        records,
        method=method,
        numeric_fields=numeric_fields,
        date_format=date_format,
        rename_map=rename_map,
    )


@mcp.tool()
def tool_compare_data(
    records: list,
    targets: dict | None = None,
    baseline: list | None = None,
    fields: list | None = None,
) -> list:
    """
    Benchmark records against targets or historical baseline.
    """
    return compare_data(records, targets=targets, baseline=baseline, fields=fields)


# ──────────────────────────────────────────────────────────────
# Consolidation tool
# ──────────────────────────────────────────────────────────────

@mcp.tool()
def tool_consolidate_report(
    processed_data: list,
    rag_context: list,
    domain: str = "",
    kpis: list | None = None,
    reporting_period: str = "",
) -> dict:
    """
    Merge all processed data and RAG context into a unified dataset for TRIZ analysis.
    """
    return consolidate_report(
        processed_data=processed_data,
        rag_context=rag_context,
        domain=domain,
        kpis=kpis or [],
        reporting_period=reporting_period,
    )


# ──────────────────────────────────────────────────────────────
# RAG tool
# ──────────────────────────────────────────────────────────────

@mcp.tool()
def tool_query_rag(query: str, top_k: int = 5) -> list:
    """
    Query the RAG knowledge base for relevant context chunks.
    Returns top_k relevant text chunks.
    """
    return query_rag(query, top_k=top_k)


# ──────────────────────────────────────────────────────────────
# Dynamic tools (créés par tool_builder)
# ──────────────────────────────────────────────────────────────

def _register_dynamic_tool(tool_name: str, tool_func):
    """
    Enregistre un outil dynamique sur le serveur MCP.
    Crée un wrapper qui expose la fonction via MCP.
    """
    # Créer un wrapper avec une signature générique
    @mcp.tool(name=f"tool_{tool_name}")
    def dynamic_tool_wrapper(**kwargs):
        """
        Outil généré dynamiquement: {tool_name}
        """
        return tool_func(**kwargs)
    
    # Mettre à jour la docstring avec celle de l'outil original si disponible
    if hasattr(tool_func, "__doc__") and tool_func.__doc__:
        dynamic_tool_wrapper.__doc__ = tool_func.__doc__


# Enregistrer tous les outils dynamiques découverts
for tool_name, tool_func in _dynamic_tools.items():
    try:
        _register_dynamic_tool(tool_name, tool_func)
        print(f"✓ Registered dynamic tool: {tool_name}")
    except Exception as e:
        print(f"✗ Failed to register tool {tool_name}: {e}")


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run(transport="http", port=8001)