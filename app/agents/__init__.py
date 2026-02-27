"""
agents package — Pipeline multi-agents Hack2Cash

Agents disponibles :
  - SupervisorAgent   : orchestrateur déterministe
  - WebResearchAgent  : recherche web + RAG (Tavily)
  - ToolBuilderAgent  : analyse de format + création d'outils
  - AnalysisAgent     : extraction KPIs + tendances + réponse NL
"""
from .supervisor_agent   import SupervisorAgent, GlobalState
from .web_research_agent import WebResearchAgent, RagChunk
from .tool_builder_agent import ToolBuilderAgent, ToolSpec
from .analysis_agent     import AnalysisAgent, AnalysisResult

__all__ = [
    "SupervisorAgent", "GlobalState",
    "WebResearchAgent", "RagChunk",
    "ToolBuilderAgent", "ToolSpec",
    "AnalysisAgent", "AnalysisResult",
]
