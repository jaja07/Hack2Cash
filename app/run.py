"""
ARIA — Main Entry Point
Usage:
    python main.py                        # exemple avec données fictives
    python main.py --file path/to/file    # analyse d'un fichier
    python main.py --stream               # mode streaming
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from agent import run_aria


def parse_args():
    parser = argparse.ArgumentParser(description="ARIA — Autonomous Report Intelligence Analyst")
    parser.add_argument("--file",     type=str, help="Path to file to analyse (pdf, csv, excel, json, txt)")
    parser.add_argument("--url",      type=str, help="URL to scrape")
    parser.add_argument("--db",       type=str, help="SQLite path or connection string")
    parser.add_argument("--db-query", type=str, help="SQL query (used with --db)")
    parser.add_argument("--query",    type=str, help="Prompt utilisateur pour orienter l'analyse")
    parser.add_argument("--formats",  type=str, default="json,markdown", help="Output formats (comma-separated)")
    parser.add_argument("--thread",   type=str, default="aria-default", help="Thread ID for checkpointing")
    parser.add_argument("--stream",   action="store_true", help="Enable streaming mode")
    return parser.parse_args()


def build_sources(args) -> list[dict]:
    """Build data_sources list from CLI arguments."""
    sources = []

    if args.file:
        ext = args.file.rsplit(".", 1)[-1].lower() if "." in args.file else "txt"
        sources.append({
            "source_id":   "cli-file",
            "source_type": "file",
            "path_or_url": args.file,
            "data_format": ext,
            "metadata":    {},
        })

    if args.url:
        sources.append({
            "source_id":   "cli-web",
            "source_type": "web",
            "path_or_url": args.url,
            "data_format": "html",
            "metadata":    {"extract_tables": True},
        })

    if args.db:
        sources.append({
            "source_id":   "cli-db",
            "source_type": "database",
            "path_or_url": args.db,
            "data_format": "sql",
            "metadata": {"query": args.db_query or "SELECT * FROM reports LIMIT 100"},
        })

    # Fallback — exemple fictif si aucune source fournie
    if not sources:
        print("⚠️  No data source provided. Running with sample data.\n")
        sources = [
            {
                "source_id":   "sample-001",
                "source_type": "file",
                "path_or_url": "sample_report.csv",
                "data_format": "csv",
                "metadata":    {},
            }
        ]

    return sources


def main():
    args    = parse_args()
    sources = build_sources(args)
    formats = [f.strip() for f in args.formats.split(",")]

    print("=" * 60)
    print("ARIA — Autonomous Report Intelligence Analyst")
    print("=" * 60)
    print(f"Sources  : {[s['source_id'] for s in sources]}")
    print(f"Formats  : {formats}")
    print(f"Thread   : {args.thread}")
    print(f"Streaming: {args.stream}")
    print("=" * 60 + "\n")

    # ── Streaming mode ────────────────────────────────────────
    if args.stream:
        print("Streaming agent steps...\n")
        for update in run_aria(
            data_sources=sources,
            output_formats=formats,
            thread_id=args.thread,
            stream=True,
            user_query=args.query or None,
        ):
            if isinstance(update, dict):
                for node_name, node_state in update.items():
                    if isinstance(node_state, dict):
                        status = node_state.get("status", "")
                        errors = node_state.get("errors", [])
                        
                        # Affichage du nœud avec son statut
                        print(f"\n{'='*60}")
                        print(f"▶ [{node_name}] {status}")
                        print(f"{'='*60}")
                        
                        # Affichage spécifique selon le nœud
                        if node_name == "domain_identifier":
                            domain = node_state.get("domain")
                            confidence = node_state.get("domain_confidence", 0)
                            kpis = node_state.get("kpis", [])
                            period = node_state.get("reporting_period")
                            if domain:
                                print(f"  📊 Domaine identifié: {domain} (confiance: {confidence*100:.1f}%)")
                            if period:
                                print(f"  📅 Période: {period}")
                            if kpis:
                                print(f"  📈 KPIs: {', '.join(kpis[:5])}")
                        
                        elif node_name == "data_extractor":
                            extracted = node_state.get("extracted_data", [])
                            if extracted:
                                print(f"  ✅ {len(extracted)} source(s) extraite(s)")
                                for src in extracted[:3]:
                                    src_id = src.get("source_id", "unknown")
                                    extractor_used = src.get("extractor_used", "unknown")
                                    data = src.get("data", {})
                                    if isinstance(data, dict):
                                        data_type = data.get("format", type(data).__name__)
                                        if "rows" in data:
                                            row_count = len(data.get("rows", []))
                                            print(f"     - {src_id}: {extractor_used} → {row_count} ligne(s) extraite(s)")
                                        else:
                                            print(f"     - {src_id}: {extractor_used} → format {data_type}")
                                    else:
                                        print(f"     - {src_id}: {extractor_used} → {type(data).__name__}")
                        
                        elif node_name == "data_operator":
                            processed = node_state.get("processed_data", [])
                            needs_tool = node_state.get("needs_tool_builder", False)
                            if needs_tool:
                                tool_spec = node_state.get("missing_tool_spec", {})
                                tool_name = tool_spec.get("tool_name", "unknown")
                                print(f"  🔧 Outil manquant détecté: {tool_name}")
                                print(f"     Description: {tool_spec.get('description', 'N/A')[:80]}")
                            elif processed:
                                print(f"  ✅ {len(processed)} jeu(x) de données traité(s)")
                        
                        elif node_name == "tool_builder_agent":
                            tool_result = node_state.get("tool_builder_result", {})
                            tool_status = tool_result.get("status", "unknown")
                            tool_name = tool_result.get("tool_name", "unknown")
                            
                            if tool_status == "success":
                                print(f"  ✅ Outil créé avec succès: {tool_name}")
                                persisted = tool_result.get("persisted_at", "")
                                if persisted:
                                    print(f"     📁 Fichier: {persisted}")
                                validated = tool_result.get("validated", False)
                                print(f"     ✓ Validé: {validated}")
                            else:
                                error = tool_result.get("error", "Unknown error")
                                print(f"  ❌ Échec création outil: {tool_name}")
                                print(f"     Erreur: {error[:200]}")
                        
                        elif node_name == "rag_retriever":
                            rag_queries = node_state.get("rag_queries", [])
                            rag_context = node_state.get("rag_context", [])
                            if rag_queries:
                                print(f"  🔍 Requêtes RAG: {len(rag_queries)}")
                                for q in rag_queries[:2]:
                                    print(f"     - {q[:60]}...")
                            if rag_context:
                                print(f"  📚 Chunks RAG récupérés: {len(rag_context)}")
                        
                        elif node_name == "data_consolidator":
                            consolidated = node_state.get("consolidated_data", {})
                            if consolidated:
                                record_count = consolidated.get("record_count", 0)
                                kpi_data = consolidated.get("kpi_data", {})
                                print(f"  ✅ Dataset consolidé: {record_count} enregistrements")
                                if kpi_data:
                                    print(f"  📊 KPIs calculés: {', '.join(list(kpi_data.keys())[:5])}")
                        
                        elif node_name == "triz_analyzer":
                            triz = node_state.get("triz_analysis", {})
                            contradictions = triz.get("contradictions", [])
                            principles = triz.get("triz_principles_applied", [])
                            findings = node_state.get("key_findings", [])
                            recommendations = node_state.get("recommendations", [])
                            confidence = node_state.get("confidence_score", 0)
                            
                            if contradictions:
                                print(f"  🔍 Contradictions identifiées: {len(contradictions)}")
                                for c in contradictions[:2]:
                                    c_type = c.get("type", "unknown").upper()
                                    improving = c.get("improving_parameter", "")
                                    degrading = c.get("degrading_parameter", "")
                                    print(f"     - {c_type}: {improving} ↑ vs {degrading} ↓")
                            
                            if principles:
                                print(f"  💡 Principes TRIZ appliqués: {len(principles)}")
                                for p in principles[:3]:
                                    p_num = p.get("principle_number", "?")
                                    p_name = p.get("name", "unknown")
                                    print(f"     - #{p_num} {p_name}")
                            
                            if findings:
                                print(f"  📌 Findings clés: {len(findings)}")
                                for f in findings[:3]:
                                    print(f"     • {f[:80]}...")
                            
                            if recommendations:
                                print(f"  💼 Recommandations: {len(recommendations)}")
                                for r in recommendations[:3]:
                                    priority = r.get("priority", "?")
                                    action = r.get("action", "")[:60]
                                    owner = r.get("owner", "?")
                                    print(f"     - [{priority}] {action}... (Owner: {owner})")
                            
                            print(f"  📊 Score de confiance: {confidence*100:.1f}%")
                        
                        elif node_name == "report_generator":
                            artifacts = node_state.get("report_artifacts", {})
                            if artifacts:
                                print(f"  📄 Rapports générés:")
                                for fmt in ["json", "markdown", "html", "pdf", "pptx"]:
                                    if fmt in artifacts:
                                        if fmt == "json":
                                            print(f"     ✓ {fmt.upper()}: en mémoire")
                                        elif isinstance(artifacts[fmt], str) and os.path.exists(artifacts[fmt]):
                                            print(f"     ✓ {fmt.upper()}: {artifacts[fmt]}")
                                        else:
                                            print(f"     ✓ {fmt.upper()}: généré")
                                if "charts" in artifacts:
                                    charts = artifacts["charts"]
                                    if isinstance(charts, list):
                                        print(f"     ✓ Graphiques: {len(charts)} fichier(s)")
                        
                        elif node_name == "error_handler":
                            iteration = node_state.get("iteration", 0)
                            degraded = node_state.get("degraded_report", False)
                            print(f"  ⚠️  Itération: {iteration}/3")
                            if degraded:
                                print(f"  ⚠️  Rapport dégradé (max retries atteint)")
                        
                        # Affichage des erreurs
                        if errors:
                            print(f"\n  ⚠️  Erreurs ({len(errors)}):")
                            for err in errors[-3:]:  # Afficher les 3 dernières erreurs
                                print(f"     - {err[:150]}")
                    else:
                        print(f"  ▶ [{node_name}]")
            else:
                print(f"  ▶ {update}")
        
        print(f"\n{'='*60}")
        print("✅ Pipeline terminé")
        print(f"{'='*60}\n")
        return

    # ── Invoke mode ───────────────────────────────────────────
    result = run_aria(
        data_sources=sources,
        output_formats=formats,
        thread_id=args.thread,
        stream=False,
        user_query=args.query or None,   # ← ajouter
    )

    if not result:
        print("❌ Agent returned no result.")
        sys.exit(1)

    # ── Print summary ─────────────────────────────────────────
    print(f"Status    : {result.get('status', 'unknown')}")
    print(f"Domain    : {result.get('domain', 'N/A')}")
    print(f"Period    : {result.get('reporting_period', 'N/A')}")
    print(f"KPIs      : {result.get('kpis', [])}")
    print(f"Confidence: {result.get('confidence_score', 0) * 100:.1f}%")
    print(f"Degraded  : {result.get('degraded_report', False)}")
    print(f"Errors    : {len(result.get('errors', []))}")

    artifacts = result.get("report_artifacts", {})
    if artifacts:
        print(f"\nArtifacts generated:")
        for fmt, val in artifacts.items():
            if isinstance(val, str) and os.path.exists(val):
                print(f"  - {fmt}: {val}")
            elif fmt == "json":
                print(f"  - {fmt}: in memory")
            elif fmt == "charts":
                print(f"  - charts: {len(val)} file(s)")
            else:
                print(f"  - {fmt}: generated")

    # ── Save markdown if requested ────────────────────────────
    if "markdown" in formats and "markdown" in artifacts:
        md_path = f"aria_report_{args.thread}.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(artifacts["markdown"])
        print(f"\n📄 Markdown saved: {md_path}")

    print("\n✅ Analysis complete.")


if __name__ == "__main__":
    main()