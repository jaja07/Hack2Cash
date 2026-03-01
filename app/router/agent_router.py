"""
router/agent_router.py
Routes FastAPI pour déclencher le pipeline ARIA.
Toutes les routes sont protégées par JWT.
"""

import os
import tempfile
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from typing import Annotated, Optional

from entity.user_entity import User
from schema.agent import AnalyzeRequest, AnalyzeResponse, AgentStatusResponse
from service.auth_service import get_current_user

router = APIRouter(prefix="/agents", tags=["Agents"])

CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Lancer le pipeline ARIA sur des sources de données",
)
def analyze(
    request: AnalyzeRequest,
    current_user: CurrentUserDep,
):
    """
    Lance le pipeline complet ARIA :
    domain_identifier → data_extractor → data_operator →
    rag_retriever → data_consolidator → triz_analyzer → report_generator
    """
    from agent import run_aria

    # Rétrocompatibilité cra_text → source texte temporaire
    sources = [s.model_dump() for s in request.data_sources]
    if request.cra_text and not sources:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        )
        tmp.write(request.cra_text)
        tmp.close()
        sources = [{
            "source_id":   "cra-text",
            "source_type": "file",
            "path_or_url": tmp.name,
            "data_format": "txt",
            "metadata":    {},
        }]

    if not sources:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one data source or cra_text.",
        )

    try:
        user_query = request.query.strip() if request.query and request.query.strip() else None

        result = run_aria(
            data_sources=sources,
            output_formats=request.output_formats,
            thread_id=request.thread_id or str(current_user.id),
            stream=False,
            user_query=user_query,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline error: {str(e)}",
        )

    return AnalyzeResponse(
        status=           result.get("status", "unknown"),
        domain=           result.get("domain"),
        reporting_period= result.get("reporting_period"),
        kpis=             result.get("kpis", []),
        confidence_score= result.get("confidence_score", 0.0),
        confidence_pct=   f"{result.get('confidence_score', 0.0) * 100:.1f}%",
        degraded_report=  result.get("degraded_report", False),
        iterations=       result.get("iteration", 0),
        key_findings=     result.get("key_findings", []),
        recommendations=  result.get("recommendations", []),
        triz_analysis=    result.get("triz_analysis"),
        artifacts=        result.get("report_artifacts", {}),
        errors=           result.get("errors", []),
        node_history=     result.get("node_history", []),
    )


@router.post(
    "/analyze/upload",
    response_model=AnalyzeResponse,
    summary="Analyser un fichier uploadé directement",
)
async def analyze_upload(
    current_user: CurrentUserDep,
    file:  UploadFile = File(...),
    query: Optional[str] = Form(None),
):

    """
    Upload un fichier et lance le pipeline ARIA directement.
    Formats supportés : pdf, csv, xlsx, json, txt.
    """
    from agent import run_aria

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else "txt"

    tmp = tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False)
    tmp.write(await file.read())
    tmp.close()

    sources = [{
        "source_id":   file.filename,
        "source_type": "file",
        "path_or_url": tmp.name,
        "data_format": ext,
        "metadata":    {},
    }]

    try:
        user_query = query.strip() if query and query.strip() else None
        result = run_aria(
            data_sources=sources,
            output_formats=["json", "markdown"],
            thread_id=str(current_user.id),
            stream=False,
            user_query=user_query,   # ← ajouter
        )
    except Exception as e:
        os.unlink(tmp.name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline error: {str(e)}",
        )

    os.unlink(tmp.name)

    return AnalyzeResponse(
        status=           result.get("status", "unknown"),
        domain=           result.get("domain"),
        reporting_period= result.get("reporting_period"),
        kpis=             result.get("kpis", []),
        confidence_score= result.get("confidence_score", 0.0),
        confidence_pct=   f"{result.get('confidence_score', 0.0) * 100:.1f}%",
        degraded_report=  result.get("degraded_report", False),
        iterations=       result.get("iteration", 0),
        key_findings=     result.get("key_findings", []),
        recommendations=  result.get("recommendations", []),
        triz_analysis=    result.get("triz_analysis"),
        artifacts=        result.get("report_artifacts", {}),
        errors=           result.get("errors", []),
        node_history=     result.get("node_history", []),
    )


@router.get(
    "/status",
    response_model=AgentStatusResponse,
    summary="Vérifier que les agents sont disponibles",
)
def agents_status(current_user: CurrentUserDep):
    return AgentStatusResponse(
        status="ok",
        agents=[
            "domain_identifier", "human_checkpoint",
            "data_extractor", "data_operator",
            "rag_retriever", "data_consolidator",
            "triz_analyzer", "report_generator",
            "error_handler",
        ],
        configured={
            "nvidia_api":      bool(os.getenv("NVIDIA_API_KEY")),
            "research_agent":  False,  # stub
            "tool_builder":    False,  # stub
        },
        user=current_user.email,
    )