from pydantic import BaseModel
from typing import Any


class AnalyzeRequest(BaseModel):
    query: str = "Analyse complète du CRA"
    domain: str = ""
    cra_text: str

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Quels sont les KPIs et tendances de ce CRA ?",
                "domain": "conseil IT",
                "cra_text": "Janvier 2024 — 22 jours facturés...",
            }
        }


class AgentStatusResponse(BaseModel):
    supervisor: str
    web_research: str
    tool_builder: str
    analysis: str


class AnalyzeResponse(BaseModel):
    status: str
    iterations: int
    agent_statuses: AgentStatusResponse
    rag_chunks_count: int
    tools_count: int
    result: dict[str, Any] | None
    error: str | None
    supervisor_notes: list[str]
