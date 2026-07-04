"""
embedding_engine.py

Generates text embeddings using Google's free Gemini embedding API.
No local model download needed -- safe for low-disk-space machines.
"""

import requests
from typing import List
from config import embedding_config
from logger import get_logger

log = get_logger("embedding_engine")


class EmbeddingEngine:
    def __init__(self):
        self.api_key = embedding_config.gemini_api_key
        self.model = embedding_config.gemini_model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:embedContent"

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set in .env")

    def embed_text(self, text: str) -> List[float]:
        headers = {"Content-Type": "application/json", "X-goog-api-key": self.api_key}
        payload = {
            "model": self.model,
            "content": {"parts": [{"text": text}]},
            "output_dimensionality": embedding_config.embedding_dimension,
        }

        response = requests.post(self.url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return data["embedding"]["values"]

    def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        for chunk in chunks:
            try:
                chunk["embedding"] = self.embed_text(chunk["text"])
            except Exception as e:
                log.error(f"Embedding failed for chunk {chunk['chunk_id']}: {e}")
                chunk["embedding"] = None
        log.info(f"Embedded {len(chunks)} chunks")
        return chunks