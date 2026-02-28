"""
Tool Builder — State Definition (LangGraph 1.0)
"""

from __future__ import annotations

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ToolSpec(TypedDict, total=False):
    """Spécification de l'outil demandé par ARIA."""
    tool_name:     str          # nom de la fonction Python
    description:   str          # ce que l'outil doit faire
    input_schema:  dict         # {param_name: type_str}
    output_schema: dict         # {field_name: type_str}
    example_usage: str          # exemple d'appel


class ToolResult(TypedDict, total=False):
    """Résultat retourné à ARIA après création."""
    tool_name:     str
    status:        str          # "success" | "failed"
    code:          str          # code Python généré
    persisted_at:  str          # chemin du fichier persisté
    validated:     bool         # validé par ARIA
    error:         str          # message d'erreur si échec


class ToolBuilderState(TypedDict, total=False):

    # ── Conversation ─────────────────────────────────────────
    messages: Annotated[list, add_messages]

    # ── Input — spec demandée par ARIA ────────────────────────
    tool_spec: ToolSpec

    # ── Génération ───────────────────────────────────────────
    generated_code:  str        # code Python brut généré par le LLM
    generation_plan: str        # raisonnement du LLM avant génération

    # ── Test & correction ────────────────────────────────────
    test_passed:     bool       # True si le code s'exécute sans erreur
    test_output:     str        # stdout / résultat du test
    test_error:      str        # traceback si échec
    fix_iteration:   int        # compteur de tentatives de correction (max 3)

    # ── Persistance ──────────────────────────────────────────
    persisted_at:    str        # chemin absolu du fichier créé

    # ── Résultat final ────────────────────────────────────────
    tool_result:     ToolResult

    # ── Contrôle ─────────────────────────────────────────────
    errors:          list[str]
    status:          str        # "running" | "done" | "failed"
    current_node:    str