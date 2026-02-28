"""
ARIA — RAG Tool (Placeholder)
Will be replaced with a real vector store implementation (e.g. ChromaDB, Pinecone, pgvector).
"""

from __future__ import annotations


def query_rag(query: str, top_k: int = 5) -> list[str]:
    """
    Query the RAG knowledge base for relevant context chunks.

    Args:
        query : Natural language query string
        top_k : Number of chunks to retrieve

    Returns:
        List of relevant text chunks

    NOTE: This is a placeholder. Connect a real vector store here.
    Supported integrations (to be implemented):
      - ChromaDB  : pip install chromadb
      - Pinecone  : pip install pinecone-client
      - pgvector  : pip install pgvector sqlalchemy
      - FAISS     : pip install faiss-cpu
      - LangChain VectorStore wrappers
    """
    # ── Placeholder response ─────────────────────────────────
    return [
        f"[RAG PLACEHOLDER] No knowledge base connected yet. Query: '{query[:80]}'",
        "To activate RAG: implement vector store connection in agent/tools/rag.py",
        f"Top-{top_k} chunks will be returned once connected.",
    ]


def index_documents(documents: list[dict]) -> dict:
    """
    Index documents into the RAG knowledge base.

    Args:
        documents : [{"id": str, "content": str, "metadata": dict}]

    Returns:
        Indexing status dict

    NOTE: Placeholder — implement vector store upsert logic here.
    """
    return {
        "status":    "placeholder",
        "indexed":   0,
        "total":     len(documents),
        "message":   "RAG indexing not yet implemented. Connect a vector store.",
    }
