"""
agents/web_research_agent.py

Agent de recherche web + RAG.
Pipeline :
  query_planner → web_searcher → content_extractor → relevance_filter → rag_formatter

Utilise Tavily pour la recherche et Deploy AI (GPT-4o) pour l'analyse.
"""
import logging
from dataclasses import dataclass, field
from typing import Any

from core.config import settings

logger = logging.getLogger(__name__)

# ── Structures de données ──────────────────────────────────────────────────────

@dataclass
class RagChunk:
    """Un chunk RAG issu d'une source web."""
    content: str
    source_url: str
    relevance_score: float = 0.0
    chunk_index: int = 0


@dataclass
class WebResearchState:
    """État interne partagé entre les nœuds du pipeline."""
    domain: str = ""
    cra_text: str = ""
    queries: list[str] = field(default_factory=list)
    raw_results: list[dict[str, Any]] = field(default_factory=list)
    extracted_contents: list[dict[str, Any]] = field(default_factory=list)
    filtered_docs: list[dict[str, Any]] = field(default_factory=list)
    rag_chunks: list[RagChunk] = field(default_factory=list)
    error: str | None = None


# ── Nœuds du pipeline ─────────────────────────────────────────────────────────

def query_planner(state: WebResearchState) -> WebResearchState:
    """
    Nœud 1 — Génère 3-5 requêtes de recherche pertinentes
    à partir du texte CRA et du domaine d'activité.
    """
    try:
        from agents.deploy_ai_client import llm_call

        prompt = f"""Tu es un expert en recherche documentaire.
Domaine d'activité : {state.domain}
Extrait du CRA : {state.cra_text[:800]}

Génère exactement 4 requêtes de recherche Google précises et complémentaires
pour enrichir l'analyse de ce compte rendu d'activités.
Réponds UNIQUEMENT avec les 4 requêtes, une par ligne, sans numérotation."""

        response = llm_call(prompt)
        state.queries = [q.strip() for q in response.strip().split("\n") if q.strip()][:4]
        logger.info(f"[web_research] {len(state.queries)} requêtes générées")
    except Exception as e:
        logger.warning(f"[web_research] query_planner fallback: {e}")
        # Requêtes de secours si Deploy AI indisponible
        state.queries = [
            f"{state.domain} tendances 2024 2025",
            f"{state.domain} indicateurs performance KPI",
            f"compte rendu activité {state.domain} analyse",
            f"{state.domain} meilleures pratiques rentabilité",
        ]
    return state


def web_searcher(state: WebResearchState) -> WebResearchState:
    """
    Nœud 2 — Exécute les requêtes via Tavily Search API.
    Retombe sur des résultats simulés si la clé API est absente.
    """
    if not settings.TAVILY_API_KEY:
        logger.warning("[web_research] TAVILY_API_KEY absente — résultats simulés")
        state.raw_results = [
            {
                "query": q,
                "results": [
                    {
                        "title": f"Article sur {q}",
                        "url": f"https://example.com/{i}",
                        "content": f"Contenu simulé pour la requête : {q}. "
                                   f"Les tendances montrent une croissance de 15% en 2024.",
                        "score": 0.85 - i * 0.05,
                    }
                    for i in range(3)
                ],
            }
            for q in state.queries
        ]
        return state

    try:
        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        for query in state.queries:
            result = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_raw_content=True,
            )
            state.raw_results.append({"query": query, "results": result.get("results", [])})
        logger.info(f"[web_research] {len(state.raw_results)} lots de résultats récupérés")
    except Exception as e:
        logger.error(f"[web_research] web_searcher error: {e}")
        state.error = str(e)
    return state


def content_extractor(state: WebResearchState) -> WebResearchState:
    """
    Nœud 3 — Extrait et nettoie les contenus depuis les résultats bruts Tavily.
    """
    for batch in state.raw_results:
        for item in batch.get("results", []):
            content = item.get("raw_content") or item.get("content") or ""
            if content:
                state.extracted_contents.append(
                    {
                        "url": item.get("url", ""),
                        "title": item.get("title", ""),
                        "content": content[:3000],  # limite à 3000 chars par source
                        "score": item.get("score", 0.5),
                    }
                )
    logger.info(f"[web_research] {len(state.extracted_contents)} documents extraits")
    return state


def relevance_filter(state: WebResearchState) -> WebResearchState:
    """
    Nœud 4 — Filtre les documents dont le score Tavily >= 0.5.
    """
    state.filtered_docs = [
        doc for doc in state.extracted_contents if doc.get("score", 0) >= 0.5
    ]
    logger.info(f"[web_research] {len(state.filtered_docs)} documents pertinents retenus")
    return state


def rag_formatter(state: WebResearchState) -> WebResearchState:
    """
    Nœud 5 — Découpe les documents en chunks RAG (512 mots, overlap 64 mots).
    """
    CHUNK_SIZE    = 512   # mots
    OVERLAP_SIZE  = 64    # mots

    chunk_idx = 0
    for doc in state.filtered_docs:
        words = doc["content"].split()
        start = 0
        while start < len(words):
            end   = min(start + CHUNK_SIZE, len(words))
            chunk = " ".join(words[start:end])
            state.rag_chunks.append(
                RagChunk(
                    content=chunk,
                    source_url=doc["url"],
                    relevance_score=doc.get("score", 0.5),
                    chunk_index=chunk_idx,
                )
            )
            chunk_idx += 1
            start += CHUNK_SIZE - OVERLAP_SIZE

    logger.info(f"[web_research] {len(state.rag_chunks)} chunks RAG générés")
    return state


# ── Point d'entrée ─────────────────────────────────────────────────────────────

class WebResearchAgent:
    """
    Agent de recherche web.
    Exécute le pipeline séquentiel et retourne les chunks RAG.
    """

    def run(self, cra_text: str, domain: str = "") -> list[RagChunk]:
        """
        Lance le pipeline complet.
        Retourne la liste de RagChunk prêts à être injectés dans le contexte LLM.
        """
        state = WebResearchState(cra_text=cra_text, domain=domain or "conseil entreprise")

        pipeline = [
            query_planner,
            web_searcher,
            content_extractor,
            relevance_filter,
            rag_formatter,
        ]

        for node in pipeline:
            state = node(state)
            if state.error:
                logger.error(f"[web_research] Pipeline interrompu : {state.error}")
                break

        return state.rag_chunks
