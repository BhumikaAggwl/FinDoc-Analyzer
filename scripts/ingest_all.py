"""
ingest_all.py

Batch ingestion pipeline: processes all filings in data/uploads/ through
extraction, chunking, embedding, vector storage, metric extraction, and
SQL storage.
"""

from pathlib import Path
from src.document_processing.document_extractor import DocumentExtractor
from src.document_processing.chunker import TextChunker
from src.embeddings.embedding_engine import EmbeddingEngine
from src.embeddings.vector_store import VectorStore
from src.financial_analysis.metrics_extractor import MetricsExtractor
from src.financial_analysis.ratio_calculator import RatioCalculator
from database.models import init_db
from database.repository import save_filing, save_metrics, save_ratios
from logger import get_logger

log = get_logger("ingest_all")

UPLOADS_DIR = Path("data/uploads")
MAX_CHUNKS_PER_DOC = 40  # limit to control disk usage / API calls

# Map filenames to company info
COMPANY_MAP = {
    "Apple": ("Apple Inc.", "AAPL"),
    "Microsoft": ("Microsoft Corporation", "MSFT"),
    "Tesla": ("Tesla Inc.", "TSLA"),
    "Amazon": ("Amazon.com Inc.", "AMZN"),
    "Nvidia": ("NVIDIA Corporation", "NVDA"),
    "Alphabet": ("Alphabet Inc.", "GOOGL"),
    "Meta": ("Meta Platforms Inc.", "META"),
}


def get_company_info(filename: str):
    for key, info in COMPANY_MAP.items():
        if key.lower() in filename.lower():
            return info
    return (filename, None)


def ingest_file(file_path: Path):
    document_id = file_path.stem  # e.g. "Apple_10K"
    filing_type = "10-K" if "10K" in document_id else "10-Q" if "10Q" in document_id else "Unknown"
    company_name, ticker = get_company_info(file_path.name)

    log.info(f"--- Ingesting {file_path.name} ---")

    try:
        extractor = DocumentExtractor(str(file_path))
        pages = extractor.extract_pages()
        full_text = extractor.extract_full_text()

        chunker = TextChunker()
        chunks = chunker.chunk_pages(pages)[:MAX_CHUNKS_PER_DOC]

        engine = EmbeddingEngine()
        embedded = engine.embed_chunks(chunks)

        store = VectorStore()
        store.add_chunks(embedded, document_id=document_id)

        metrics = MetricsExtractor().extract_metrics(full_text)
        ratios = RatioCalculator(metrics).calculate_all()

        filing_id = save_filing(
            document_id=document_id,
            file_name=file_path.name,
            company_name=company_name,
            filing_type=filing_type,
            ticker=ticker
        )
        save_metrics(filing_id, metrics)
        save_ratios(filing_id, ratios)

        log.info(f"Completed ingestion for {document_id}")

    except Exception as e:
        log.error(f"Failed to ingest {file_path.name}: {e}")


def ingest_all():
    init_db()
    files = list(UPLOADS_DIR.glob("*.htm")) + list(UPLOADS_DIR.glob("*.pdf"))
    log.info(f"Found {len(files)} files to ingest")

    for file_path in files:
        ingest_file(file_path)

    log.info("Batch ingestion complete")


if __name__ == "__main__":
    ingest_all()