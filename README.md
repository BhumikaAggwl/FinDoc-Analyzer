# FinDoc AI — Financial Statement Intelligence Platform

AI-powered equity research assistant that reads 10-Ks, 10-Qs, and annual reports the way a junior equity research analyst would — grounded in retrieved document evidence, not hallucinated.

## What it does

Upload or ingest a financial filing (10-K, 10-Q, annual report), and the system:

- Extracts and cleans document text (PDF or HTML/SEC EDGAR)
- Chunks and embeds the content for semantic search
- Retrieves relevant sections to answer natural-language questions, with page-level citations
- Extracts key financial metrics (revenue, net income, EPS, margins, etc.)
- Calculates standard financial ratios (ROE, ROA, D/E, current ratio, etc.)
- Generates a BUY / HOLD / SELL recommendation with a confidence score and rationale
- Persists structured data in SQL and unstructured embeddings in a vector store
- 
## Demo

![FinDoc AI Dashboard](assets/dashboard_screenshot.png)

*Chat interface answering a question about Apple's 10-K risk factors, with page-level citations and sidebar showing extracted metrics, ratios, and investment recommendation.*

## Architecture

```
Upload filing (PDF/HTML)
        │
        ▼
Document extractor (PyMuPDF / BeautifulSoup)
        │
        ▼
Chunker (overlapping text chunks, page-tracked)
        │
        ├──────────────────────────┐
        ▼                          ▼
Embedding engine (Gemini)   Metrics extractor
        │                          │
        ▼                          ▼
Vector store (ChromaDB)     Ratio calculator
        │                          │
        ▼                          ▼
   Retriever                 SQLite (SQLAlchemy)
        │                          │
        ▼                          │
RAG pipeline (Groq LLM,             │
  analyst system prompt)            │
        │                          │
        └───────────┬──────────────┘
                     ▼
          Investment recommender
                     │
                     ▼
              Streamlit chat UI
```

## Tech stack

| Layer | Technology |
|---|---|
| Document parsing | PyMuPDF, BeautifulSoup |
| Embeddings | Google Gemini embedding API |
| Vector database | ChromaDB (persistent, local) |
| LLM generation | Groq (Llama 3.3 70B) |
| Structured storage | SQLite + SQLAlchemy ORM |
| UI | Streamlit |
| Language | Python 3.11, fully typed, modular architecture |

## Design rationale

**Why RAG instead of fine-tuning.** Fine-tuning bakes a fixed set of facts into model weights — it's the wrong tool when the actual requirement is "answer questions about whichever document was just uploaded," including documents the model has never seen, for companies it may never be retrained on. RAG keeps the LLM generic and grounds every answer in text retrieved from the specific filing at query time. This is also what makes citation possible: because the answer is built from retrieved, page-tagged chunks, the system can point to "page 22" rather than asserting a fact from opaque model weights. It mirrors how real institutional research tools (Bloomberg, FactSet, AlphaSense) are built — retrieval over a document corpus, not a fine-tuned model per client or per filing.

**Why the data is split across a vector store and a SQL database.** These two stores hold fundamentally different kinds of data and are queried in different ways. Narrative content — risk factors, MD&A, business description — has no fixed schema and is retrieved by semantic similarity to a question, which is exactly what a vector database is built for. Financial metrics and ratios, by contrast, are structured, named, and typed values (revenue is always a number, EPS is always a number) — the kind of data relational databases are built for, with joins across companies and filings and exact-match queries like "give me every filing where debt-to-equity exceeds X." Storing metrics in the vector store would mean losing the ability to query them precisely; storing narrative in SQL would mean losing semantic search. Splitting them is not extra complexity for its own sake — it is using each store for what it is actually good at, and it is what production financial data platforms do (structured fundamentals in a warehouse or relational store, unstructured filings/transcripts in a document/vector index).

**What would change at scale.** This project runs on SQLite and a local ChromaDB instance, which is correct for one user and a handful of filings but would not hold up under real load. At scale: SQLite would move to Postgres for concurrent writes and proper transaction isolation; ChromaDB would move to a managed vector database (e.g. Pinecone, Weaviate, or pgvector on top of Postgres) to support horizontal scaling and higher-throughput similarity search across thousands of filings; the regex-based metric extraction would be replaced with direct XBRL tag parsing, since every SEC filing already carries machine-readable structured tags for exactly these line items, which is both more reliable and removes an entire class of extraction bugs; and the single-process ingestion script would become a queued, async pipeline (e.g. Celery or a task queue) so uploading a large filing doesn't block the request thread. None of these are architectural rewrites — the module boundaries here (extractor, chunker, embedding engine, vector store, retriever, repository) are designed so each one is a drop-in replacement behind the same interface.

## Setup

```bash
git clone <repo>
cd findoc_ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env`:
```
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
LLM_PROVIDER=groq
EMBEDDING_PROVIDER=gemini
```

Ingest sample filings:
```bash
python scripts/download_filings.py
python -m scripts.ingest_all
```

Run the app:
```bash
streamlit run app/Home.py
```

## Known limitations (and what a v2 would do)

- **Metric extraction is regex/proximity-based**, not table-structure-aware. It can mis-pick numbers adjacent to a keyword rather than the actual line-item value. A production version would parse XBRL tags directly (SEC filings are XBRL-tagged) or use `pdfplumber` table extraction for structured statements, giving reliable figures instead of best-effort text matching.
- **Single-document analysis only.** Multi-document comparison (e.g. Apple vs Microsoft, QoQ trends) is architected for — the SQL schema already supports it — but not yet built into the UI.
- **No backtesting or quantitative validation** of the BUY/HOLD/SELL output against actual price performance; the recommendation is a qualitative LLM synthesis of retrieved narrative and available ratios, not a validated quant signal.

## Roadmap

- XBRL-based structured metric extraction (replace regex extraction)
- Multi-document comparison view (cross-company, cross-quarter)
- A supervised ML classifier (scikit-learn) trained on historical ratio data as a secondary, quantitative check alongside the LLM's qualitative recommendation
- Earnings call transcript ingestion
- Altman Z-Score / Piotroski F-Score as first-class computed fields

