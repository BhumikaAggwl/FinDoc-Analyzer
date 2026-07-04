"""
retriever.py

Given a natural-language question, retrieves the most relevant document
chunks from the vector store using semantic similarity search.
"""

from typing import List, Dict
from src.embeddings.embedding_engine import EmbeddingEngine
from src.embeddings.vector_store import VectorStore
from logger import get_logger

log = get_logger("retriever")


class Retriever:
    def __init__(self):
        self.embedding_engine = EmbeddingEngine()
        self.vector_store = VectorStore()

    def retrieve(self, query: str, document_id: str = None, top_k: int = None) -> List[Dict]:
        """
        Returns relevant chunks for a query, each with text, page_number, distance.
        """
        query_embedding = self.embedding_engine.embed_text(query)
        results = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=top_k,
            document_id=document_id
        )
        log.info(f"Retrieved {len(results)} chunks for query: '{query[:60]}...'")
        return results

    def build_context(self, query: str, document_id: str = None, top_k: int = None) -> str:
        """
        Returns a single formatted context string (with page citations)
        ready to inject into an LLM prompt.
        """
        results = self.retrieve(query, document_id=document_id, top_k=top_k)

        context_blocks = []
        for r in results:
            page = r["metadata"]["page_number"]
            text = r["text"]
            context_blocks.append(f"[Page {page}]\n{text}")

        return "\n\n---\n\n".join(context_blocks)