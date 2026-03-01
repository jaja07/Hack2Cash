"""
ARIA — Node Implementations (LangGraph 1.0)
Each node applies sliding window memory before any LLM call.
"""

from __future__ import annotations

import json
from datetime import datetime

from langgraph.types import interrupt

from langchain_core.messages import HumanMessage, AIMessage

from agent.global_variable.system_prompt import SYSTEM_PROMPT
from agent.llm_provider.base_llm import BaseLLMProvider
from agent.memory.sliding_window import apply_sliding_window
from agent.agent_config.state import ARIAState


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def _llm() -> BaseLLMProvider:
    return BaseLLMProvider(system_prompt=SYSTEM_PROMPT, max_tokens=8192)

def _now() -> str:
    return datetime.utcnow().isoformat()

def _record_node(state: ARIAState, name: str, status: str, summary: str) -> dict:
    entry = {"node": name, "timestamp": _now(), "status": status, "summary": summary}
    history = list(state.get("node_history", []))
    history.append(entry)
    return {"current_node": name, "node_history": history}

def _record_decision(state: ARIAState, node: str, condition: str, outcome: str, reason: str) -> dict:
    entry = {"node": node, "condition": condition, "outcome": outcome, "reason": reason}
    decisions = list(state.get("decisions", []))
    decisions.append(entry)
    return {"decisions": decisions}

def _windowed_context(state: ARIAState) -> str | None:
    """Apply sliding window and return compressed context string for LLM injection."""
    messages = state.get("messages", [])
    if not messages:
        return None
    windowed = apply_sliding_window(messages)
    # Extract summary message if compression occurred
    from langchain_core.messages import SystemMessage
    for msg in windowed:
        if isinstance(msg, SystemMessage) and "[PREVIOUS CONTEXT]" in msg.content:
            return msg.content
    return None

def _user_query_block(state: ARIAState) -> str:
    uq = state.get("user_query")
    if not uq:
        return ""
    return (
        f"\n>>> USER INSTRUCTION (priorité haute — oriente toute l'analyse) :\n"
        f'"{uq}"\n'
        f"Tiens impérativement compte de cette instruction pour choisir le domaine, "
        f"les KPIs, les opérations, et les findings.\n\n"
    )

# ──────────────────────────────────────────────────────────────
# NODE 1 — domain_identifier
# ──────────────────────────────────────────────────────────────

def _preview_sources(sources: list) -> str:
    """Read a small preview of each source to help domain identification."""
    import os
    previews = []
    for src in sources:
        src_type = src.get("source_type", "file")
        path     = src.get("path_or_url", "")
        fmt      = src.get("data_format", "").lower()
        preview  = {"source_id": src.get("source_id"), "source_type": src_type}

        if src_type == "file" and os.path.exists(path):
            try:
                if fmt == "csv":
                    import pandas as pd
                    df = pd.read_csv(path, nrows=5)
                    preview["columns"] = df.columns.tolist()
                    preview["sample_rows"] = df.head(3).to_dict(orient="records")
                elif fmt in ("xlsx", "xls", "excel"):
                    import pandas as pd
                    df = pd.read_excel(path, nrows=5)
                    preview["columns"] = df.columns.tolist()
                    preview["sample_rows"] = df.head(3).to_dict(orient="records")
                elif fmt == "json":
                    with open(path, "r") as f:
                        data = json.load(f)
                    preview["sample"] = data if isinstance(data, dict) else data[:3]
                else:
                    with open(path, "r", errors="replace") as f:
                        preview["sample_text"] = f.read(500)
            except Exception as e:
                preview["preview_error"] = str(e)
        else:
            preview["note"] = "Non-file source or file not found — metadata only"

        previews.append(preview)
    return json.dumps(previews, indent=2, default=str)


def domain_identifier(state: ARIAState) -> dict:
    viz     = _record_node(state, "domain_identifier", "running", "Identifying domain, period, and KPIs")
    llm     = _llm()
    context = _windowed_context(state)
    sources = state.get("data_sources", [])
    errors  = list(state.get("errors", []))

    data_preview = _preview_sources(sources)
    user_query_ctx = _user_query_block(state)
    has_files      = bool(sources)

    prompt = f"""
    {user_query_ctx}
REASONING STEP — answer before acting:
1. What do the data columns and sample rows tell us about the domain?
{"(No file provided — infer domain from the USER INSTRUCTION above.)" if not has_files else ""}
2. Is the domain clear enough (confidence ≥ 0.6) to proceed, or should I ask the user?
3. Is this domain specific enough to require the research agent?

Data preview (columns + sample rows):
{data_preview}

Task: identify domain, reporting period, KPIs, and confidence.

Respond ONLY with valid JSON:
{{
  "reasoning": "<your step-by-step reasoning>",
  "domain": "<domain>",
  "reporting_period": "<period>",
  "kpis": ["kpi1", "kpi2"],
  "domain_confidence": 0.85,
  "needs_research_agent": false,
  "clarification_question": null
}}
"""
    result = llm.invoke_for_json(prompt, context=context)
    raw_response = json.dumps(result) if result else ""

    if not result:
        errors.append("domain_identifier: LLM returned invalid JSON")
        return {**viz, "errors": errors, "domain_confidence": 0.0,
                "domain": "unknown", "status": "running"}

    decision = _record_decision(
        state, "domain_identifier",
        f"confidence={result.get('domain_confidence', 0)}",
        "proceed" if result.get("domain_confidence", 0) >= 0.6 else "human_checkpoint",
        result.get("reasoning", "")
    )

    return {
        **viz, **decision,
        "messages": [HumanMessage(content=prompt), AIMessage(content=raw_response)],
        "domain":             result.get("domain", "unknown"),
        "reporting_period":   result.get("reporting_period", "unknown"),
        "kpis":               result.get("kpis", []),
        "domain_confidence":  result.get("domain_confidence", 0.0),
        "needs_research_agent": result.get("needs_research_agent", False),
        "clarification_question": result.get("clarification_question"),
        "errors": errors,
        "status": "running",
    }


# ──────────────────────────────────────────────────────────────
# NODE 2 — human_checkpoint
# ──────────────────────────────────────────────────────────────

def human_checkpoint(state: ARIAState) -> dict:
    viz = _record_node(state, "human_checkpoint", "waiting", "Waiting for human domain confirmation")

    human_input = interrupt({
        "question": (
            f"I identified the domain as **{state.get('domain', 'unknown')}** "
            f"(confidence: {state.get('domain_confidence', 0):.0%}). "
            f"{state.get('clarification_question') or 'Please confirm or correct.'}"
        ),
        "current_domain":   state.get("domain"),
        "current_period":   state.get("reporting_period"),
        "suggested_kpis":   state.get("kpis", []),
    })

    return {
        **viz,
        "domain":            human_input.get("domain") or state.get("domain"),
        "reporting_period":  human_input.get("reporting_period") or state.get("reporting_period"),
        "kpis":              human_input.get("kpis") or state.get("kpis", []),
        "domain_confidence": 1.0,
        "status": "running",
    }


# ──────────────────────────────────────────────────────────────
# NODE 3 — data_extractor
# ──────────────────────────────────────────────────────────────

def data_extractor(state: ARIAState) -> dict:
    viz = _record_node(state, "data_extractor", "running", "Extracting data from all sources")

    from agent.tools.extract import (
        extract_from_file, extract_from_database,
        extract_from_api, extract_from_web
    )
    import agent.tools as tools_module
    import importlib
    import inspect
    import sys
    
    # ── Découvrir dynamiquement les extracteurs disponibles ─────
    def _discover_extractors():
        """Découvre tous les extracteurs disponibles, y compris ceux créés dynamiquement."""
        extractors = {
            "file":     extract_from_file,
            "database": extract_from_database,
            "api":      extract_from_api,
            "web":      extract_from_web,
        }
        
        # Recharger le module tools pour prendre en compte les nouveaux outils
        # Utiliser reload seulement si le module est déjà chargé
        if tools_module.__name__ in sys.modules:
            try:
                importlib.reload(tools_module)
            except Exception:
                pass  # Si le reload échoue, continuer avec les outils déjà chargés
        
        # Chercher les fonctions extract_from_* dans le module tools
        for name, obj in inspect.getmembers(tools_module, inspect.isfunction):
            if name.startswith("extract_from_") and name not in [
                "extract_from_file", "extract_from_database", 
                "extract_from_api", "extract_from_web"
            ]:
                # Extraire le format du nom (ex: extract_from_xml -> xml)
                format_name = name.replace("extract_from_", "")
                extractors[format_name] = obj
        
        return extractors
    
    EXTRACTOR_MAP = _discover_extractors()

    sources        = state.get("data_sources", [])
    extracted_data = []
    errors         = list(state.get("errors", []))
    iteration      = state.get("iteration", 0)

    for src in sources:
        src_type  = src.get("source_type", "file")
        data_format = src.get("data_format", "").lower()
        
        # ── Choisir l'extracteur approprié ──────────────────────
        extractor_name = None
        # Si c'est un fichier, essayer d'utiliser un extracteur spécifique au format
        if src_type == "file" and data_format:
            # Chercher un extracteur spécifique pour ce format (ex: extract_from_xml pour xml)
            extractor = EXTRACTOR_MAP.get(data_format) or EXTRACTOR_MAP.get("file")
            if data_format in EXTRACTOR_MAP:
                extractor_name = f"extract_from_{data_format}"
            else:
                extractor_name = "extract_from_file"
        else:
            # Utiliser l'extracteur par défaut pour le type de source
            extractor = EXTRACTOR_MAP.get(src_type, extract_from_file)
            extractor_name = f"extract_from_{src_type}" if src_type in EXTRACTOR_MAP else "extract_from_file"
        
        try:
            data = extractor(src)
            extracted_data.append({
                "source_id":    src.get("source_id"),
                "source_type":  src_type,
                "data":         data,
                "extracted_at": _now(),
                "extractor_used": extractor_name,  # Stocker l'extracteur utilisé
            })
        except Exception as e:
            errors.append(f"data_extractor [{src.get('source_id')}]: {str(e)}")

    return {
        **viz,
        "extracted_data": extracted_data,
        "errors":         errors,
        "iteration":      iteration + 1,
    }


# ──────────────────────────────────────────────────────────────
# NODE 4 — data_operator
# ──────────────────────────────────────────────────────────────

def data_operator(state: ARIAState) -> dict:
    viz     = _record_node(state, "data_operator", "running", "Transforming and enriching extracted data")
    llm     = _llm()
    context = _windowed_context(state)
    errors  = list(state.get("errors", []))

    from agent.tools.operations import filter_data, aggregate_data, normalize_data, compare_data
    import agent.tools as tools_module
    import inspect
    import sys

    OP_MAP = {
        "filter":    filter_data,
        "aggregate": aggregate_data,
        "normalize": normalize_data,
        "compare":   compare_data,
    }

    # ── Détecter format non supporté → déclencher tool_builder ─
    for src_data in state.get("extracted_data", []):
        data = src_data.get("data", {})
        if isinstance(data, dict) and data.get("format") == "unknown":
            path = data.get("path", "")
            ext  = path.rsplit(".", 1)[-1].lower() if "." in path else "unknown"
            return {
                **viz,
                "needs_tool_builder": True,
                "missing_tool_spec": {
                    "tool_name":     f"extract_from_{ext}",
                    "description":   f"Extract and parse structured data from {ext.upper()} files into a list of dicts",
                    "input_schema":  {"source": "dict with path_or_url and metadata"},
                    "output_schema": {"rows": "list[dict]", "columns": "list[str]"},
                    "example_usage": f"extract_from_{ext}({{'path_or_url': 'file.{ext}', 'metadata': {{}}}})",
                },
                "errors": errors,
            }

    # ── Liste des outils disponibles dans agent/tools/ ────────
    # Recharger le module pour découvrir les nouveaux outils créés
    import importlib
    importlib.reload(tools_module)
    
    available_tools = [
        name for name, obj in inspect.getmembers(tools_module, inspect.isfunction)
    ]

    user_query_ctx = _user_query_block(state)

    prompt = f"""
{user_query_ctx} REASONING STEP:
1. Given domain "{state.get('domain')}" and KPIs {state.get('kpis', [])},
   which operations are necessary and in what order?
2. {"The user instruction MUST influence which fields to filter, group, or prioritize." if state.get("user_query") else "No specific user instruction."}
3. Are the available ops (filter, aggregate, normalize, compare) sufficient?
4. If not, describe precisely the missing tool needed.

Available tools in agent/tools: {available_tools}
Extracted data sample: {json.dumps(state.get('extracted_data', [])[:1], default=str)[:1000]}

Respond ONLY with valid JSON:
{{
  "reasoning": "<your reasoning>",
  "operations": [{{"op": "normalize", "params": {{}}}}],
  "missing_tool": {{
    "needed": false,
    "tool_name": null,
    "description": null,
    "input_schema": {{}},
    "output_schema": {{}},
    "example_usage": null
  }}
}}
"""
    plan     = llm.invoke_for_json(prompt, context=context)
    raw_plan = json.dumps(plan) if plan else ""

    if not plan:
        plan = {"operations": [{"op": "normalize", "params": {}}], "missing_tool": {"needed": False}}

    # ── Outil manquant détecté → déléguer au tool_builder ─────
    missing = plan.get("missing_tool", {})
    if missing.get("needed") and missing.get("tool_name"):
        missing_spec = {
            "tool_name":     missing.get("tool_name"),
            "description":   missing.get("description", ""),
            "input_schema":  missing.get("input_schema", {}),
            "output_schema": missing.get("output_schema", {}),
            "example_usage": missing.get("example_usage", ""),
        }
        return {
            **viz,
            "messages":          [HumanMessage(content=prompt), AIMessage(content=raw_plan)],
            "needs_tool_builder": True,
            "missing_tool_spec":  missing_spec,
            "errors":             errors,
        }

    # ── Normaliser les params LLM → signature réelle ─────────
    def _normalize_params(op: str, params: dict) -> dict:
        if op == "aggregate":
            gb = params.get("group_by") or params.get("groupby")
            if isinstance(gb, list):
                gb = gb[0] if gb else None

            aggs = params.get("aggregations") or params.get("metrics") or {}

            if isinstance(aggs, dict):
                metrics = [{"field": f, "op": op_} for f, op_ in aggs.items()]
            elif isinstance(aggs, list):
                # Normaliser : string → {"field": str, "op": "sum"}
                metrics = []
                for item in aggs:
                    if isinstance(item, str):
                        metrics.append({"field": item, "op": "sum"})
                    elif isinstance(item, dict):
                        metrics.append({
                            "field": item.get("field", ""),
                            "op":    item.get("op", "sum"),
                        })
            else:
                metrics = []

            return {"group_by": gb, "metrics": metrics}

        if op == "normalize":
            # columns → numeric_fields
            fields = params.get("numeric_fields") or params.get("columns") or params.get("fields")
            # method: min_max → minmax
            method = params.get("method", "minmax").replace("_", "").replace("-", "").lower()
            if method not in ("minmax", "zscore", "none"):
                method = "minmax"
            return {"numeric_fields": fields, "method": method}

        if op == "compare":
            # metrics liste → fields
            metrics = params.get("metrics") or params.get("fields")
            if isinstance(metrics, list) and metrics and isinstance(metrics[0], str):
                params = {**params, "fields": metrics}
            return {k: v for k, v in params.items() if k not in ("metrics", "comparison_method")}

        return params

    # ── Appliquer les opérations disponibles ──────────────────
    processed = list(state.get("extracted_data", []))
    for op_def in plan.get("operations", []):
        op_name = op_def.get("op")
        fn      = OP_MAP.get(op_name)
        if fn:
            try:
                clean_params = _normalize_params(op_name, op_def.get("params", {}))
                processed = fn(processed, **clean_params)
            except Exception as e:
                errors.append(f"data_operator [{op_name}]: {str(e)}")

    return {
        **viz,
        "messages":           [HumanMessage(content=prompt), AIMessage(content=raw_plan)],
        "processed_data":     processed,
        "needs_tool_builder": False,
        "errors":             errors,
    }


# ──────────────────────────────────────────────────────────────
# NODE 5 — rag_retriever
# ──────────────────────────────────────────────────────────────

def rag_retriever(state: ARIAState) -> dict:
    viz = _record_node(state, "rag_retriever", "running", "Querying RAG knowledge base")

    from agent.tools.rag import query_rag

    domain  = state.get("domain", "")
    kpis    = state.get("kpis", [])
    period  = state.get("reporting_period", "")
    errors  = list(state.get("errors", []))

    queries = [
        f"{domain} activity report benchmarks {period}",
        f"{domain} KPI standards: {', '.join(kpis[:3])}",
        f"historical trends {domain} {period}",
    ]

    user_query = state.get("user_query")
    if user_query:
        queries.append(f"{domain} {user_query[:100]}")

    rag_context = []
    for q in queries:
        try:
            chunks = query_rag(q)
            rag_context.extend(chunks if isinstance(chunks, list) else [chunks])
        except Exception as e:
            errors.append(f"rag_retriever: {str(e)}")

    return {**viz, "rag_queries": queries, "rag_context": rag_context, "errors": errors}


# ──────────────────────────────────────────────────────────────
# NODE 6 — data_consolidator
# ──────────────────────────────────────────────────────────────

def data_consolidator(state: ARIAState) -> dict:
    viz = _record_node(state, "data_consolidator", "running", "Consolidating all data into unified dataset")
    errors = list(state.get("errors", []))

    from agent.tools.consolidation import consolidate_report
    try:
        consolidated = consolidate_report(
            processed_data=state.get("processed_data", []),
            rag_context=state.get("rag_context", []),
            domain=state.get("domain", ""),
            kpis=state.get("kpis", []),
            reporting_period=state.get("reporting_period", ""),
        )
    except Exception as e:
        errors.append(f"data_consolidator: {str(e)}")
        consolidated = {
            "domain":   state.get("domain"),
            "period":   state.get("reporting_period"),
            "kpis":     state.get("kpis"),
            "data":     state.get("processed_data", []),
            "rag":      state.get("rag_context", []),
            "fallback": True,
        }

    return {**viz, "consolidated_data": consolidated, "errors": errors}


# ──────────────────────────────────────────────────────────────
# NODE 7 — triz_analyzer
# ──────────────────────────────────────────────────────────────

def triz_analyzer(state: ARIAState) -> dict:
    viz     = _record_node(state, "triz_analyzer", "running", "Applying TRIZ analysis")
    llm     = _llm()
    context = _windowed_context(state)
    errors  = list(state.get("errors", []))

    consolidated = state.get("consolidated_data", {})
    iteration    = state.get("iteration", 0)

    user_query_ctx = _user_query_block(state)

    prompt = f"""
{user_query_ctx}REASONING STEP:
1. What are the main contradictions visible in this dataset?
{"2. The user instruction MUST orient the findings and recommendations." if state.get("user_query") else "2. No specific user instruction."}
3. What is the Ideal Final Result (IFR) for this domain?
4. Which TRIZ inventive principles apply to each contradiction?
5. What are the root causes (not symptoms)?

Domain: {state.get('domain')} | Period: {state.get('reporting_period')} | KPIs: {state.get('kpis')}
Consolidated dataset (truncated):
{json.dumps(consolidated, indent=2, default=str)[:5000]}

Respond ONLY with valid JSON:
{{
  "reasoning": "<step-by-step reasoning>",
  "contradictions": [
    {{
      "type": "technical|physical",
      "improving_parameter": "",
      "degrading_parameter": "",
      "description": ""
    }}
  ],
  "ideal_final_result": "",
  "triz_principles_applied": [
    {{"principle_number": 1, "name": "Segmentation", "application": ""}}
  ],
  "root_causes": [],
  "cross_analysis": {{
    "time_vs_kpi": [],
    "department_vs_kpi": [],
    "insights": []
  }},
  "key_findings": [],
  "recommendations": [
    {{"action": "", "owner": "", "timeline": "", "priority": "High|Medium|Low"}}
  ],
  "confidence_score": 0.85,
  "confidence_rationale": "",
  "degraded_report": {str(iteration >= 3).lower()}
}}
"""

    result = llm.invoke_for_json(prompt, context=context)
    raw_result = json.dumps(result) if result else ""

    if not result:
        errors.append("triz_analyzer: LLM returned invalid JSON")
        return {**viz, "triz_analysis": {}, "confidence_score": 0.0, "errors": errors}

    triz = {
        "contradictions":        result.get("contradictions", []),
        "ideal_final_result":    result.get("ideal_final_result", ""),
        "triz_principles_applied": result.get("triz_principles_applied", []),
        "root_causes":           result.get("root_causes", []),
        "cross_analysis":        result.get("cross_analysis", {}),
    }

    confidence = float(result.get("confidence_score", 0.5))
    decision   = _record_decision(
        state, "triz_analyzer",
        f"confidence={confidence:.2f}, iteration={iteration}",
        "report_generator" if confidence >= 0.70 or iteration >= 3 else "data_extractor",
        result.get("confidence_rationale", "")
    )

    return {
        **viz, **decision,
        "messages":         [HumanMessage(content=prompt), AIMessage(content=raw_result)],
        "triz_analysis":    triz,
        "key_findings":     result.get("key_findings", []),
        "recommendations":  result.get("recommendations", []),
        "confidence_score": confidence,
        "degraded_report":  iteration >= 3 and confidence < 0.70,
        "errors":           errors,
    }


# ──────────────────────────────────────────────────────────────
# NODE 8 — report_generator
# ──────────────────────────────────────────────────────────────

def report_generator(state: ARIAState) -> dict:
    viz    = _record_node(state, "report_generator", "running", "Generating final report")
    errors = list(state.get("errors", []))

    from agent.tools.renderers import render_markdown, render_html, render_pdf, render_pptx
    from agent.tools.visualizations import render_charts

    # LAYER 1 — Structured JSON
    final_report = {
        "1_overview": {
            "domain":          state.get("domain"),
            "reporting_period": state.get("reporting_period"),
            "kpis":            state.get("kpis", []),
            "data_sources":    [s.get("source_id") for s in state.get("data_sources", [])],
            "user_query":       state.get("user_query"),
            "generated_at":    _now(),
            "degraded":        state.get("degraded_report", False),
        },
        "2_data_summary": {
            "consolidated_dataset": state.get("consolidated_data", {}),
            "rag_chunks_used":      len(state.get("rag_context", [])),
        },
        "3_triz_analysis":   state.get("triz_analysis", {}),
        "4_key_findings":    state.get("key_findings", []),
        "5_recommendations": state.get("recommendations", []),
        "6_confidence": {
            "score":    state.get("confidence_score", 0.0),
            "percent":  f"{state.get('confidence_score', 0.0) * 100:.1f}%",
            "degraded": state.get("degraded_report", False),
        },
    }

    # LAYER 2 — Rendered artifacts
    output_formats = state.get("output_formats", ["json", "markdown", "html", "pdf", "pptx"])
    artifacts: dict = {"json": final_report}
    chart_paths = []

    try:
        chart_paths = render_charts(final_report)
        artifacts["charts"] = chart_paths
    except Exception as e:
        errors.append(f"render_charts: {str(e)}")

    for fmt, fn in [("markdown", render_markdown), ("html", lambda r: render_html(r, chart_paths))]:
        if fmt in output_formats:
            try:
                artifacts[fmt] = fn(final_report)
            except Exception as e:
                errors.append(f"render_{fmt}: {str(e)}")

    for fmt, fn in [("pdf", render_pdf), ("pptx", render_pptx)]:
        if fmt in output_formats:
            try:
                artifacts[fmt] = fn(final_report, chart_paths)
            except Exception as e:
                errors.append(f"render_{fmt}: {str(e)}")

    return {
        **viz,
        "final_report":     final_report,
        "report_artifacts": artifacts,
        "errors":           errors,
        "status":           "done",
    }


# ──────────────────────────────────────────────────────────────
# NODE 9 — error_handler
# ──────────────────────────────────────────────────────────────

def error_handler(state: ARIAState) -> dict:
    viz       = _record_node(state, "error_handler", "running", "Handling errors and deciding retry")
    iteration = state.get("iteration", 0)
    decision  = _record_decision(
        state, "error_handler",
        f"iteration={iteration}",
        "data_extractor" if iteration < 3 else "report_generator",
        "Retrying extraction" if iteration < 3 else "Max retries reached — generating degraded report",
    )
    return {
        **viz, **decision,
        "errors":          state.get("errors", []),
        "degraded_report": iteration >= 3,
        "status":          "running",
    }