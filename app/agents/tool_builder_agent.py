"""
agents/tool_builder_agent.py

Agent de construction d'outils d'analyse.
Pipeline :
  format_detector → schema_analyzer → tools_designer → tools_validator

Analyse le format du fichier CRA et génère les ToolSpec adaptés.
"""
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── Structures de données ──────────────────────────────────────────────────────

@dataclass
class ToolSpec:
    """Spécification d'un outil d'analyse généré dynamiquement."""
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    implementation_hint: str = ""


@dataclass
class ToolBuilderState:
    """État interne partagé entre les nœuds du pipeline."""
    cra_text: str = ""
    filename: str = ""
    detected_format: str = "unknown"
    schema_info: dict[str, Any] = field(default_factory=dict)
    tool_specs: list[ToolSpec] = field(default_factory=list)
    validation_report: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


# ── Nœuds du pipeline ─────────────────────────────────────────────────────────

def format_detector(state: ToolBuilderState) -> ToolBuilderState:
    """
    Nœud 1 — Détecte le format du CRA (tabulaire, textuel, mixte, JSON…).
    """
    text = state.cra_text.lower()
    filename = state.filename.lower()

    if filename.endswith((".csv", ".xlsx", ".xls")):
        state.detected_format = "tabular"
    elif filename.endswith(".json"):
        state.detected_format = "json"
    elif filename.endswith(".pdf"):
        state.detected_format = "pdf"
    elif filename.endswith((".docx", ".doc")):
        state.detected_format = "document"
    else:
        # Heuristique sur le contenu
        has_table  = any(sep in text for sep in ["\t", ",", ";", "|"])
        has_numbers = sum(c.isdigit() for c in text) > len(text) * 0.05
        has_prose   = len(text.split()) > 200

        if has_table and has_prose:
            state.detected_format = "mixed"
        elif has_table:
            state.detected_format = "tabular"
        else:
            state.detected_format = "textual"

    logger.info(f"[tool_builder] Format détecté : {state.detected_format}")
    return state


def schema_analyzer(state: ToolBuilderState) -> ToolBuilderState:
    """
    Nœud 2 — Analyse le schéma du CRA (colonnes, champs, structure).
    Utilise le LLM si disponible, sinon analyse basique.
    """
    try:
        from agents.deploy_ai_client import llm_call

        prompt = f"""Analyse la structure de ce compte rendu d'activités.
Format détecté : {state.detected_format}
Extrait : {state.cra_text[:1000]}

Identifie :
1. Les champs / colonnes principaux
2. Les types de données (numérique, date, texte)
3. Les KPIs potentiellement calculables

Réponds en JSON compact avec les clés : fields, data_types, potential_kpis"""

        response = llm_call(prompt)
        # Tentative de parse JSON, sinon on garde la réponse brute
        import json, re
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            state.schema_info = json.loads(match.group())
        else:
            state.schema_info = {"raw_analysis": response}

    except Exception as e:
        logger.warning(f"[tool_builder] schema_analyzer fallback: {e}")
        # Schéma générique de secours
        state.schema_info = {
            "fields": ["date", "activité", "durée", "commentaire"],
            "data_types": {"date": "date", "durée": "float", "activité": "string"},
            "potential_kpis": ["total_jours", "taux_realisation", "activites_principales"],
        }

    logger.info(f"[tool_builder] Schéma analysé : {list(state.schema_info.keys())}")
    return state


def tools_designer(state: ToolBuilderState) -> ToolBuilderState:
    """
    Nœud 3 — Conçoit les ToolSpec adaptés au format et schéma détectés.
    """
    fmt = state.detected_format

    # Outil 1 : Extracteur de KPIs (toujours présent)
    state.tool_specs.append(ToolSpec(
        name="kpi_extractor",
        description="Extrait et calcule les KPIs du CRA (jours facturés, taux de réalisation, livrables)",
        input_schema={"cra_text": "str", "schema_info": "dict"},
        output_schema={"kpis": "dict[str, float]", "unit": "str"},
        implementation_hint=f"Adapté au format {fmt}",
    ))

    # Outil 2 : Analyseur de tendances
    state.tool_specs.append(ToolSpec(
        name="trend_analyzer",
        description="Identifie les tendances temporelles et les évolutions dans les données CRA",
        input_schema={"cra_text": "str", "rag_context": "list[str]"},
        output_schema={"trends": "list[str]", "trend_scores": "list[float]"},
        implementation_hint="Croise les données locales avec le contexte RAG",
    ))

    # Outil 3 : Moteur NL Query
    state.tool_specs.append(ToolSpec(
        name="nlq_engine",
        description="Répond aux questions en langage naturel sur le CRA en s'appuyant sur le RAG",
        input_schema={"question": "str", "cra_text": "str", "rag_chunks": "list[str]"},
        output_schema={"answer": "str", "confidence": "float", "sources": "list[str]"},
        implementation_hint="Augmenté avec les chunks RAG web",
    ))

    # Outil 4 : Chart Builder (si données tabulaires)
    if fmt in ("tabular", "mixed", "json"):
        state.tool_specs.append(ToolSpec(
            name="chart_builder",
            description="Génère des visualisations (bar, pie, line) à partir des données structurées",
            input_schema={"data": "dict", "chart_type": "str", "title": "str"},
            output_schema={"chart_path": "str", "chart_url": "str"},
            implementation_hint="Utilise matplotlib pour générer les graphiques",
        ))

    logger.info(f"[tool_builder] {len(state.tool_specs)} outils créés")
    return state


def tools_validator(state: ToolBuilderState) -> ToolBuilderState:
    """
    Nœud 4 — Valide que chaque ToolSpec est cohérente et complète.
    """
    issues = []
    for spec in state.tool_specs:
        if not spec.name:
            issues.append("Un outil n'a pas de nom")
        if not spec.description:
            issues.append(f"L'outil {spec.name} n'a pas de description")
        if not spec.input_schema:
            issues.append(f"L'outil {spec.name} n'a pas de schéma d'entrée")

    state.validation_report = {
        "tools_count": len(state.tool_specs),
        "tools_valid": len(state.tool_specs) - len(issues),
        "issues": issues,
        "status": "ok" if not issues else "warnings",
    }
    logger.info(f"[tool_builder] Validation : {state.validation_report['status']}")
    return state


# ── Point d'entrée ─────────────────────────────────────────────────────────────

class ToolBuilderAgent:
    """
    Agent de construction d'outils.
    Analyse le CRA et génère les ToolSpec adaptés.
    """

    def run(self, cra_text: str, filename: str = "") -> list[ToolSpec]:
        """
        Lance le pipeline et retourne la liste de ToolSpec prêts à utiliser.
        """
        state = ToolBuilderState(cra_text=cra_text, filename=filename)

        pipeline = [
            format_detector,
            schema_analyzer,
            tools_designer,
            tools_validator,
        ]

        for node in pipeline:
            state = node(state)
            if state.error:
                logger.error(f"[tool_builder] Pipeline interrompu : {state.error}")
                break

        return state.tool_specs
