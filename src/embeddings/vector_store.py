"""
vector_store.py

Stores and retrieves document chunk embeddings using ChromaDB (local, free,
lightweight -- persists to disk, no server needed).
"""

import chromadb
from typing import List, Dict
from config import vector_store_config
from logger import get_logger

log = get_logger("vector_store")


class VectorStore:
    def __init__(self, collection_name: str = None):
        self.client = chromadb.PersistentClient(path=vector_store_config.persist_directory)
        self.collection_name = collection_name or vector_store_config.collection_name
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def add_chunks(self, chunks: List[Dict], document_id: str):
        """
        chunks: list of dicts with keys chunk_id, page_number, text, embedding
        document_id: unique identifier for the source document (e.g. filename)
        """
        ids, embeddings, documents, metadatas = [], [], [], []

        for chunk in chunks:
            if chunk.get("embedding") is None:
                continue
            unique_id = f"{document_id}_chunk_{chunk['chunk_id']}"
            ids.append(unique_id)
            embeddings.append(chunk["embedding"])
            documents.append(chunk["text"])
            metadatas.append({
                "document_id": document_id,
                "page_number": chunk["page_number"],
                "chunk_id": chunk["chunk_id"],
            })

        if not ids:
            log.warning("No valid embeddings to add to vector store")
            return

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        log.info(f"Added {len(ids)} chunks to vector store for document '{document_id}'")

    def query(self, query_embedding: List[float], top_k: int = None, document_id: str = None) -> List[Dict]:
        """
        Returns top_k most relevant chunks for a given query embedding.
        Optionally filter by document_id.
        """
        top_k = top_k or vector_store_config.top_k_results
        where_filter = {"document_id": document_id} if document_id else None

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter,
        )

        matches = []
        for i in range(len(results["ids"][0])):
            matches.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i],
            })
        return matches

    def delete_document(self, document_id: str):
        """Removes all chunks belonging to a specific document."""
        self.collection.delete(where={"document_id": document_id})
        log.info(f"Deleted all chunks for document '{document_id}'")