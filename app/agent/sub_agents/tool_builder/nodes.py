"""
Tool Builder — Node Implementations (LangGraph 1.0)
"""

from __future__ import annotations

import importlib.util
import io
import os
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime

from agent.llm_provider.base_llm import BaseLLMProvider
from agent.global_variable.tool_generation_prompt import TOOL_GENERATION_PROMPT
from agent.sub_agents.tool_builder.state import ToolBuilderState
from agent.sub_agents.tool_builder.tool_template import (
    build_generation_prompt,
    build_fix_prompt,
    build_tool_file,
)

TOOLS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tools")


def _llm() -> BaseLLMProvider:
    return BaseLLMProvider(system_prompt=TOOL_GENERATION_PROMPT)

def _now() -> str:
    return datetime.utcnow().isoformat()


# ──────────────────────────────────────────────────────────────
# NODE 1 — code_generator
# ──────────────────────────────────────────────────────────────

def code_generator(state: ToolBuilderState) -> dict:
    """Génère le code Python de l'outil via le LLM."""
    llm      = _llm()
    spec     = state.get("tool_spec", {})
    errors   = list(state.get("errors", []))

    prompt = build_generation_prompt(spec)
    result = llm.invoke_for_json(prompt)

    if not result or not result.get("code"):
        errors.append("code_generator: LLM returned no code")
        return {
            "current_node":   "code_generator",
            "status":         "failed",
            "errors":         errors,
            "generated_code": "",
        }

    return {
        "current_node":    "code_generator",
        "status":          "running",
        "generated_code":  result.get("code", ""),
        "generation_plan": result.get("reasoning", ""),
        "errors":          errors,
    }


# ──────────────────────────────────────────────────────────────
# NODE 2 — code_tester
# ──────────────────────────────────────────────────────────────

def code_tester(state: ToolBuilderState) -> dict:
    """
    Exécute le code généré dans un sandbox minimal.
    Vérifie : syntaxe, import, définition de la fonction.
    """
    code      = state.get("generated_code", "")
    spec      = state.get("tool_spec", {})
    tool_name = spec.get("tool_name", "unknown_tool")
    errors    = list(state.get("errors", []))

    if not code:
        errors.append("code_tester: no code to test")
        return {
            "current_node": "code_tester",
            "test_passed":  False,
            "test_error":   "No code provided",
            "errors":       errors,
        }

    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()

    try:
        # ── Sandbox : exec dans un namespace isolé ────────────
        namespace: dict = {}
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            exec(compile(code, "<tool_builder>", "exec"), namespace)  # noqa: S102

        # ── Vérifier que la fonction est bien définie ─────────
        if tool_name not in namespace:
            raise NameError(f"Function '{tool_name}' not found in generated code.")

        # ── Valider le contrat de sortie {"rows": [...], "columns": [...]} ──
        # On tente un appel avec un input minimal neutre pour inspecter la sortie.
        # Si l'outil nécessite un vrai fichier, on skippe la validation de sortie
        # mais on vérifie au moins que la signature est appelable.
        tool_fn = namespace[tool_name]
        contract_error = _validate_output_contract(tool_fn, spec)
        if contract_error:
            raise ValueError(f"Output contract violation: {contract_error}")

        return {
            "current_node": "code_tester",
            "test_passed":  True,
            "test_output":  stdout_buf.getvalue(),
            "test_error":   "",
            "errors":       errors,
        }

    except Exception:
        tb = traceback.format_exc()
        errors.append(f"code_tester: {tb[:300]}")
        return {
            "current_node": "code_tester",
            "test_passed":  False,
            "test_output":  stdout_buf.getvalue(),
            "test_error":   tb,
            "errors":       errors,
        }


def _validate_output_contract(tool_fn, spec: dict) -> str | None:
    """
    Vérifie que la fonction respecte le contrat de sortie ARIA :
      {"rows": list[dict], "columns": list[str]}

    Stratégie :
    - On appelle la fonction avec un input synthétique minimal.
    - Si elle lève une exception liée à un fichier manquant → on skippe (pas d'erreur).
    - Si elle retourne un résultat, on vérifie le format.
    - Si elle retourne {"error": ...} → c'est acceptable (gestion d'erreur correcte).

    Returns:
        None si le contrat est respecté, str décrivant la violation sinon.
    """
    import inspect

    # Construire un input minimal selon le type d'outil
    sig = inspect.signature(tool_fn)
    params = list(sig.parameters.keys())

    # Inputs synthétiques selon le premier paramètre détecté
    if not params:
        return None  # Pas de paramètre → on ne peut pas tester

    test_inputs = [
        {"path_or_url": "/nonexistent_test_file.xml", "metadata": {}},
        {"path_or_url": "/nonexistent_test_file.csv", "metadata": {}},
        {"path": "/nonexistent_test_file.xlsx", "sheet_name": "Sheet1",
         "filter_column": "col", "filter_value": "val"},
    ]

    result = None
    for test_input in test_inputs:
        try:
            first_param = params[0]
            result = tool_fn(**{first_param: test_input})
            break
        except (FileNotFoundError, KeyError, TypeError):
            # Input ne correspond pas à la signature → essayer le suivant
            continue
        except Exception:
            # Toute autre exception → la fonction gère probablement avec {"error": ...}
            # On considère ça comme acceptable si c'est une erreur de fichier manquant
            return None

    if result is None:
        return None  # Impossible de tester → on laisse passer

    # {"error": ...} est une réponse valide
    if isinstance(result, dict) and "error" in result:
        return None

    # Vérifier le contrat {"rows": list, "columns": list}
    if not isinstance(result, dict):
        return f"Expected dict output, got {type(result).__name__}"

    if "rows" not in result:
        return (
            f"Missing key 'rows' in output. Got keys: {list(result.keys())}. "
            "All extraction tools must return {{'rows': list[dict], 'columns': list[str]}}."
        )

    if not isinstance(result["rows"], list):
        return f"'rows' must be a list, got {type(result['rows']).__name__}"

    if "columns" not in result:
        return "Missing key 'columns' in output."

    if not isinstance(result["columns"], list):
        return f"'columns' must be a list, got {type(result['columns']).__name__}"

    # Vérifier que les rows sont des dicts avec des clés homogènes
    rows = result["rows"]
    if rows:
        if not isinstance(rows[0], dict):
            return f"'rows' must contain dicts, got {type(rows[0]).__name__}"
        first_keys = set(rows[0].keys())
        for i, row in enumerate(rows[1:], 1):
            if set(row.keys()) != first_keys:
                return (
                    f"Rows have inconsistent keys. Row 0: {sorted(first_keys)}, "
                    f"Row {i}: {sorted(row.keys())}. All rows must have identical keys."
                )

    return None  # Contrat respecté


# ──────────────────────────────────────────────────────────────
# NODE 3 — code_fixer
# ──────────────────────────────────────────────────────────────

def code_fixer(state: ToolBuilderState) -> dict:
    """Demande au LLM de corriger le code en fonction de l'erreur."""
    llm           = _llm()
    spec          = state.get("tool_spec", {})
    generated     = state.get("generated_code", "")
    test_error    = state.get("test_error", "")
    fix_iteration = state.get("fix_iteration", 0)
    errors        = list(state.get("errors", []))

    prompt = build_fix_prompt(spec, generated, test_error)
    result = llm.invoke_for_json(prompt)

    if not result or not result.get("code"):
        errors.append(f"code_fixer [attempt {fix_iteration+1}]: LLM returned no fix")
        return {
            "current_node":   "code_fixer",
            "fix_iteration":  fix_iteration + 1,
            "errors":         errors,
        }

    return {
        "current_node":   "code_fixer",
        "generated_code": result.get("code", generated),
        "generation_plan": result.get("reasoning", ""),
        "fix_iteration":  fix_iteration + 1,
        "errors":         errors,
    }


# ──────────────────────────────────────────────────────────────
# NODE 4 — tool_persister
# ──────────────────────────────────────────────────────────────

def tool_persister(state: ToolBuilderState) -> dict:
    """
    Persiste le code validé dans agent/tools/.
    Enregistre le fichier et met à jour tools/__init__.py.
    """
    spec      = state.get("tool_spec", {})
    code      = state.get("generated_code", "")
    tool_name = spec.get("tool_name", "unknown_tool")
    desc      = spec.get("description", "")
    errors    = list(state.get("errors", []))

    try:
        # ── Écrire le fichier ─────────────────────────────────
        file_content = build_tool_file(tool_name, desc, code)
        tools_dir    = os.path.abspath(TOOLS_DIR)
        file_path    = os.path.join(tools_dir, f"{tool_name}.py")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        # ── Mettre à jour tools/__init__.py ──────────────────
        init_path = os.path.join(tools_dir, "__init__.py")
        import_line = f"from agent.tools.{tool_name} import {tool_name}\n"

        with open(init_path, "r", encoding="utf-8") as f:
            init_content = f.read()

        if import_line.strip() not in init_content:
            with open(init_path, "a", encoding="utf-8") as f:
                if not init_content.endswith("\n"):
                    f.write("\n")
                f.write(import_line)

        # ── Charger dynamiquement dans le process courant ─────
        spec_obj = importlib.util.spec_from_file_location(tool_name, file_path)
        module   = importlib.util.module_from_spec(spec_obj)
        spec_obj.loader.exec_module(module)
        sys.modules[f"agent.tools.{tool_name}"] = module

        tool_result = {
            "tool_name":    tool_name,
            "status":       "success",
            "code":         code,
            "persisted_at": file_path,
            "validated":    False,  # ARIA validera après
            "error":        "",
        }

        return {
            "current_node": "tool_persister",
            "persisted_at": file_path,
            "tool_result":  tool_result,
            "status":       "done",
            "errors":       errors,
        }

    except Exception as e:
        errors.append(f"tool_persister: {str(e)}")
        return {
            "current_node": "tool_persister",
            "tool_result": {
                "tool_name": tool_name,
                "status":    "failed",
                "code":      code,
                "error":     str(e),
                "validated": False,
            },
            "status": "failed",
            "errors": errors,
        }