"""
ARIA — Agent State Definition (LangGraph 1.0)
"""

from __future__ import annotations

from typing import Annotated, Any
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class DataSource(TypedDict, total=False):
    source_id:   str
    source_type: str    # "file" | "database" | "api" | "web"
    path_or_url: str
    data_format: str    # "pdf" | "csv" | "excel" | "json" | "txt" | ...
    metadata:    dict


class TrizAnalysis(TypedDict, total=False):
    contradictions:          list   # [{type, improving_parameter, degrading_parameter, description}]
    ideal_final_result:      str
    triz_principles_applied: list   # [{principle_number, name, application}]
    root_causes:             list
    cross_analysis:          dict   # {time_vs_kpi, department_vs_kpi, insights}


class ReportArtifacts(TypedDict, total=False):
    json:     dict
    markdown: str
    html:     str
    pdf:      str
    pptx:     str
    charts:   list[str]


class ARIAState(TypedDict, total=False):

    # ── Conversation history (accumulates via add_messages reducer) ──
    messages: Annotated[list, add_messages]

    # ── Domain context ───────────────────────────────────────────────
    domain:                  str
    domain_confidence:       float
    reporting_period:        str
    kpis:                    list[str]
    clarification_question:  str     # question ciblée à poser à l'utilisateur si besoin

    # ── Sub-agents flags ─────────────────────────────────────────────
    needs_research_agent:    bool    # agent de recherche documentaire
    needs_tool_builder:      bool    # agent de création d'outils
    missing_tool_spec:       dict    # spec de l'outil manquant à créer
    tool_builder_result:     dict    # résultat retourné par le tool_builder

    # ── Data pipeline ────────────────────────────────────────────────
    data_sources:            list[DataSource]
    user_query:              str | None  
    extracted_data:          list[dict]
    processed_data:          list[dict]
    consolidated_data:       dict

    # ── RAG ──────────────────────────────────────────────────────────
    rag_context:             list[str]
    rag_queries:             list[str]

    # ── TRIZ Analysis ────────────────────────────────────────────────
    triz_analysis:           TrizAnalysis
    key_findings:            list[str]
    recommendations:         list[dict]   # [{action, owner, timeline, priority}]
    confidence_score:        float
    degraded_report:         bool         # True si max retries atteint avec confiance < 0.70

    # ── Output ───────────────────────────────────────────────────────
    output_formats:          list[str]    # ["json","markdown","html","pdf","pptx"]
    final_report:            dict
    report_artifacts:        ReportArtifacts

    # ── Graph metadata ───────────────────────────────────────────────
    current_node:            str
    node_history:            list[dict]   # [{node, timestamp, status, summary}]
    decisions:               list[dict]   # [{node, condition, outcome, reason}]

    # ── Control flow ─────────────────────────────────────────────────
    iteration:               int
    errors:                  list[str]
    status:                  str          # "running"|"waiting_human"|"done"|"failed"