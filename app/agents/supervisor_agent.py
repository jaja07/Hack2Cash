"""
agents/supervisor_agent.py

Agent superviseur — orchestrateur du pipeline multi-agents.
Séquence :
  [1] web_research_agent  →  chunks RAG
  [2] tool_builder_agent  →  ToolSpec
  [3] analysis_agent      →  AnalysisResult
  [FINISH]

Gère le GlobalState partagé et les logs d'orchestration.
"""
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── GlobalState ────────────────────────────────────────────────────────────────

@dataclass
class GlobalState:
    """
    État global partagé entre tous les agents.
    Représente le contexte complet d'une exécution du pipeline.
    """
    # Inputs
    cra_text: str = ""
    filename: str = ""
    query: str = "Analyse complète du CRA"
    domain: str = ""

    # Résultats intermédiaires
    rag_chunks: list[Any] = field(default_factory=list)
    tool_specs: list[Any] = field(default_factory=list)

    # Résultat final
    analysis_result: Any = None

    # Métadonnées d'orchestration
    iteration: int = 0
    supervisor_notes: list[str] = field(default_factory=list)
    agent_statuses: dict[str, str] = field(default_factory=lambda: {
        "supervisor":   "running",
        "web_research": "idle",
        "tool_builder": "idle",
        "analysis":     "idle",
    })
    error: str | None = None


# ── Superviseur ────────────────────────────────────────────────────────────────

class SupervisorAgent:
    """
    Orchestrateur déterministe du pipeline multi-agents Hack2Cash.

    Routing :
      START → web_research → tool_builder → analysis → FINISH

    En cas d'erreur dans un agent, note l'erreur et continue
    avec des valeurs de secours pour ne pas bloquer le pipeline.
    """

    def _log(self, state: GlobalState, msg: str) -> None:
        note = f"[Itération {state.iteration}] {msg}"
        state.supervisor_notes.append(note)
        logger.info(note)

    def _set_status(self, state: GlobalState, agent: str, status: str) -> None:
        state.agent_statuses[agent] = status

    # ── Étape 1 : Web Research ─────────────────────────────────────────────────
    def _run_web_research(self, state: GlobalState) -> GlobalState:
        state.iteration += 1
        self._set_status(state, "web_research", "running")
        self._log(state, "→ web_research_agent | Démarrage de la recherche web + RAG")

        try:
            from agents.web_research_agent import WebResearchAgent
            chunks = WebResearchAgent().run(
                cra_text=state.cra_text,
                domain=state.domain,
            )
            state.rag_chunks = chunks
            self._set_status(state, "web_research", "completed")
            self._log(state, f"✓ web_research_agent | {len(chunks)} chunks RAG générés")
        except Exception as e:
            state.rag_chunks = []
            self._set_status(state, "web_research", "failed")
            self._log(state, f"✗ web_research_agent | Erreur : {e} — pipeline continue")
            logger.error(f"[supervisor] web_research error: {e}")

        return state

    # ── Étape 2 : Tool Builder ─────────────────────────────────────────────────
    def _run_tool_builder(self, state: GlobalState) -> GlobalState:
        state.iteration += 1
        self._set_status(state, "tool_builder", "running")
        self._log(state, "→ tool_builder_agent | Analyse du format et création des outils")

        try:
            from agents.tool_builder_agent import ToolBuilderAgent
            specs = ToolBuilderAgent().run(
                cra_text=state.cra_text,
                filename=state.filename,
            )
            state.tool_specs = specs
            self._set_status(state, "tool_builder", "completed")
            self._log(state, f"✓ tool_builder_agent | {len(specs)} outils créés")
        except Exception as e:
            state.tool_specs = []
            self._set_status(state, "tool_builder", "failed")
            self._log(state, f"✗ tool_builder_agent | Erreur : {e} — pipeline continue")
            logger.error(f"[supervisor] tool_builder error: {e}")

        return state

    # ── Étape 3 : Analysis ────────────────────────────────────────────────────
    def _run_analysis(self, state: GlobalState) -> GlobalState:
        state.iteration += 1
        self._set_status(state, "analysis", "running")
        self._log(state, "→ analysis_agent | Extraction KPIs + tendances + réponse NL")

        try:
            from agents.analysis_agent import AnalysisAgent

            rag_context = [c.content for c in state.rag_chunks[:10]]
            result = AnalysisAgent().run(
                cra_text=state.cra_text,
                query=state.query,
                rag_context=rag_context,
            )
            state.analysis_result = result
            self._set_status(state, "analysis", "completed")
            self._log(
                state,
                f"✓ analysis_agent | {len(result.kpis)} KPIs, "
                f"{len(result.trends)} tendances, "
                f"{len(result.recommendations)} recommandations",
            )
        except Exception as e:
            state.error = str(e)
            self._set_status(state, "analysis", "failed")
            self._log(state, f"✗ analysis_agent | Erreur critique : {e}")
            logger.error(f"[supervisor] analysis error: {e}")

        return state

    # ── Point d'entrée ────────────────────────────────────────────────────────
    def run(
        self,
        cra_text: str,
        query: str = "Analyse complète du CRA",
        filename: str = "",
        domain: str = "",
    ) -> GlobalState:
        """
        Exécute le pipeline complet et retourne le GlobalState final.
        """
        state = GlobalState(
            cra_text=cra_text,
            query=query,
            filename=filename,
            domain=domain or "conseil entreprise",
        )

        self._log(state, "=== Démarrage du pipeline Hack2Cash ===")
        self._set_status(state, "supervisor", "completed")

        state = self._run_web_research(state)
        state = self._run_tool_builder(state)
        state = self._run_analysis(state)

        self._log(state, "=== Pipeline terminé ===")
        return state

    def to_api_response(self, state: GlobalState) -> dict:
        """Sérialise le GlobalState en dict JSON-serializable pour l'API."""
        result = state.analysis_result
        return {
            "status":      "completed" if not state.error else "failed",
            "iterations":  state.iteration,
            "agent_statuses": state.agent_statuses,
            "supervisor_notes": state.supervisor_notes,
            "rag_chunks_count": len(state.rag_chunks),
            "tools_count":     len(state.tool_specs),
            "result": {
                "summary":         result.summary         if result else "",
                "kpis":            result.kpis            if result else {},
                "trends":          result.trends          if result else [],
                "recommendations": result.recommendations if result else [],
                "nl_answer":       result.nl_answer       if result else "",
                "confidence":      result.confidence      if result else 0.0,
            } if result else None,
            "error": state.error,
        }
