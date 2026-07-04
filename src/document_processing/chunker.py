"""
chunker.py

Splits extracted PDF page text into overlapping chunks suitable for
embedding and retrieval, while preserving page number metadata.
"""

from typing import List, Dict
from config import chunking_config
from logger import get_logger

log = get_logger("chunker")


class TextChunker:
    """Splits document pages into overlapping chunks for embedding."""

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or chunking_config.chunk_size
        self.chunk_overlap = chunk_overlap or chunking_config.chunk_overlap
        self.min_chunk_size = chunking_config.min_chunk_size

    def chunk_pages(self, pages: List[Dict]) -> List[Dict]:
        """
        Input: [{"page_number": 1, "text": "..."}, ...]
        Output: [{"chunk_id": 0, "page_number": 1, "text": "..."}, ...]
        """
        chunks = []
        chunk_id = 0

        for page in pages:
            page_number = page["page_number"]
            words = page["text"].split()

            start = 0
            while start < len(words):
                end = start + self.chunk_size
                chunk_words = words[start:end]
                chunk_text = " ".join(chunk_words)

                if len(chunk_text.strip()) >= self.min_chunk_size:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "page_number": page_number,
                        "text": chunk_text
                    })
                    chunk_id += 1

                start += self.chunk_size - self.chunk_overlap

        log.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
        return chunks