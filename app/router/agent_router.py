"""
router/agent_router.py
Routes FastAPI pour déclencher le pipeline multi-agents.
Toutes les routes sont protégées par JWT.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status

from model.user_entity import User
from schema.agent import AnalyzeRequest, AnalyzeResponse
from service.auth_service import get_current_user

router = APIRouter(prefix="/agents", tags=["Agents"])

CurrentUserDep = Annotated[User, Depends(get_current_user)]


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Lancer le pipeline multi-agents sur un CRA",
)
def analyze_cra(
    request: AnalyzeRequest,
    current_user: CurrentUserDep,
):
    """
    Lance le pipeline complet :
    web_research → tool_builder → analysis

    Requiert un Bearer JWT valide.
    """
    try:
        from agents.supervisor_agent import SupervisorAgent

        supervisor = SupervisorAgent()
        state = supervisor.run(
            cra_text=request.cra_text,
            query=request.query,
            domain=request.domain,
        )
        return supervisor.to_api_response(state)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur du pipeline : {str(e)}",
        )


@router.get(
    "/status",
    summary="Vérifier que les agents sont disponibles",
)
def agents_status(current_user: CurrentUserDep):
    """Retourne le statut de disponibilité des agents."""
    from core.config import settings

    return {
        "agents": ["supervisor", "web_research", "tool_builder", "analysis"],
        "deploy_ai_configured": bool(settings.CLIENT_ID and settings.CLIENT_SECRET),
        "tavily_configured":    bool(settings.TAVILY_API_KEY),
        "user": current_user.email,
    }
