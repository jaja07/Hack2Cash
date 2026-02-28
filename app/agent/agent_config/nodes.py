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
    return BaseLLMProvider(system_prompt=SYSTEM_PROMPT)

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

    prompt = f"""
REASONING STEP — answer before acting:
1. What do the data columns and sample rows tell us about the domain?
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
    EXTRACTOR_MAP = {
        "file":     extract_from_file,
        "database": extract_from_database,
        "api":      extract_from_api,
        "web":      extract_from_web,
    }

    sources        = state.get("data_sources", [])
    extracted_data = []
    errors         = list(state.get("errors", []))
    iteration      = state.get("iteration", 0)

    for src in sources:
        src_type  = src.get("source_type", "file")
        extractor = EXTRACTOR_MAP.get(src_type, extract_from_file)
        try:
            data = extractor(src)
            extracted_data.append({
                "source_id":    src.get("source_id"),
                "source_type":  src_type,
                "data":         data,
                "extracted_at": _now(),
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
    OP_MAP = {
        "filter":    filter_data,
        "aggregate": aggregate_data,
        "normalize": normalize_data,
        "compare":   compare_data,
    }

    prompt = f"""
REASONING STEP:
1. Given domain "{state.get('domain')}" and KPIs {state.get('kpis', [])},
   which operations are necessary and in what order?
2. Are the available ops (filter, aggregate, normalize, compare) sufficient?

Respond ONLY with valid JSON:
{{
  "reasoning": "<your reasoning>",
  "operations": [{{"op": "normalize", "params": {{}}}}]
}}
"""
    plan = llm.invoke_for_json(prompt, context=context)
    raw_plan = json.dumps(plan) if plan else ""
    if not plan:
        plan = {"operations": [{"op": "normalize", "params": {}}]}

    processed = list(state.get("extracted_data", []))
    for op_def in plan.get("operations", []):
        fn = OP_MAP.get(op_def.get("op"))
        if fn:
            try:
                processed = fn(processed, **op_def.get("params", {}))
            except Exception as e:
                errors.append(f"data_operator [{op_def.get('op')}]: {str(e)}")

    return {
        **viz,
        "messages":      [HumanMessage(content=prompt), AIMessage(content=raw_plan)],
        "processed_data": processed,
        "errors":         errors,
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

    prompt = f"""
REASONING STEP:
1. What are the main contradictions visible in this dataset?
2. What is the Ideal Final Result (IFR) for this domain?
3. Which TRIZ inventive principles apply to each contradiction?
4. What are the root causes (not symptoms)?

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