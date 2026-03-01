"""
schema/agent.py
Pydantic schemas pour le pipeline ARIA.
"""

from pydantic import BaseModel
from typing import Any, Optional


class DataSourceSchema(BaseModel):
    source_id:   str
    source_type: str            # "file" | "database" | "api" | "web"
    path_or_url: str
    data_format: str = ""       # "pdf" | "csv" | "excel" | "json" | "txt" | ...
    metadata:    dict = {}

    class Config:
        json_schema_extra = {
            "example": {
                "source_id":   "report-001",
                "source_type": "file",
                "path_or_url": "/uploads/report_q1.csv",
                "data_format": "csv",
                "metadata":    {},
            }
        }


class AnalyzeRequest(BaseModel):
    data_sources:   list[DataSourceSchema] = []
    output_formats: list[str] = ["json", "markdown"]
    thread_id:      str = "aria-default"
    cra_text:       Optional[str] = None
    query:          Optional[str] = None
    domain:         Optional[str] = None

    @model_validator(mode="after")
    def at_least_one_input(self) -> "AnalyzeRequest":
        if not self.data_sources and not self.query and not self.cra_text:
            raise ValueError("Provide at least one data_source, a query, or cra_text.")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "data_sources": [...],
                "output_formats": ["json", "markdown"],
                "thread_id": "session-abc123",
            }
        }


class AnalyzeResponse(BaseModel):
    status:           str
    domain:           Optional[str]
    reporting_period: Optional[str]
    kpis:             list[str]
    confidence_score: float
    confidence_pct:   str
    degraded_report:  bool
    iterations:       int
    key_findings:     list[str]
    recommendations:  list[dict]
    triz_analysis:    Optional[dict]
    artifacts:        dict[str, Any]
    errors:           list[str]
    node_history:     list[dict]


class AgentStatusResponse(BaseModel):
    status:     str = "ok"
    agents:     list[str]
    configured: dict[str, bool]
    user:       str