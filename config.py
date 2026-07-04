"""
config.py

Centralized configuration for FinDoc AI.
All paths, model names, chunking parameters, and API settings
are defined here so every module reads from a single source of truth.

LLM inference runs entirely via FREE ONLINE APIs (Groq by default).
No local LLM is downloaded or run -- safe for low-spec machines.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# BASE PATHS
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
VECTOR_DB_DIR = DATA_DIR / "vector_db"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

for directory in [DATA_DIR, UPLOADS_DIR, VECTOR_DB_DIR, REPORTS_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# LLM PROVIDER CONFIGURATION (FREE ONLINE APIs ONLY)
# ---------------------------------------------------------------------------

@dataclass
class LLMConfig:
    """
    provider options:
        "groq"      -> FREE. Fast cloud inference. Default. (https://console.groq.com)
        "anthropic" -> Paid/credit-based. Claude models. Optional upgrade later.
    """
    provider: str = os.getenv("LLM_PROVIDER", "groq")

    # ---- Groq (FREE) ----
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")  # free, strong model
    groq_base_url: str = "https://api.groq.com/openai/v1"

    # ---- Anthropic (optional, paid) ----
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    max_tokens: int = 2048
    temperature: float = 0.2  # low -> factual, analyst-style tone


# ---------------------------------------------------------------------------
# EMBEDDING CONFIGURATION
# Lightweight local math model (NOT an LLM) -- ~80MB, CPU only, runs on any Mac
# ---------------------------------------------------------------------------

@dataclass
class EmbeddingConfig:
    provider: str = os.getenv("EMBEDDING_PROVIDER", "gemini")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "models/gemini-embedding-001"
    embedding_dimension: int = 768
    batch_size: int = 32
# ---------------------------------------------------------------------------
# CHUNKING CONFIGURATION
# ---------------------------------------------------------------------------

@dataclass
class ChunkingConfig:
    chunk_size: int = 800
    chunk_overlap: int = 150
    min_chunk_size: int = 100


# ---------------------------------------------------------------------------
# VECTOR STORE CONFIGURATION
# ---------------------------------------------------------------------------

@dataclass
class VectorStoreConfig:
    persist_directory: str = str(VECTOR_DB_DIR)
    collection_name: str = "findoc_documents"
    top_k_results: int = 6


# ---------------------------------------------------------------------------
# DOCUMENT SECTION KEYWORDS
# ---------------------------------------------------------------------------

SECTION_KEYWORDS = {
    "business_overview": ["business overview", "our business", "company overview", "who we are"],
    "risk_factors": ["risk factors", "risks and uncertainties", "principal risks"],
    "mdna": ["management's discussion and analysis", "md&a", "management discussion"],
    "financial_statements": ["consolidated balance sheet", "consolidated statement of income",
                              "consolidated statements of cash flows", "income statement"],
    "segment_reporting": ["segment information", "reportable segments", "geographic information"],
    "capital_allocation": ["share repurchase", "dividends", "capital allocation", "buyback"],
    "liquidity": ["liquidity and capital resources", "liquidity discussion"],
    "forward_looking": ["forward-looking statements", "safe harbor", "guidance"],
    "accounting_policies": ["significant accounting policies", "critical accounting estimates"],
    "esg": ["sustainability", "environmental, social", "esg", "corporate responsibility"],
}


# ---------------------------------------------------------------------------
# FINANCIAL METRIC KEYWORDS
# ---------------------------------------------------------------------------

FINANCIAL_METRIC_ALIASES = {
    "revenue": ["total revenue", "net revenue", "net sales", "total net sales"],
    "gross_profit": ["gross profit", "gross margin"],
    "operating_income": ["operating income", "income from operations"],
    "net_income": ["net income", "net earnings", "profit for the year"],
    "eps": ["earnings per share", "diluted earnings per share", "basic earnings per share"],
    "ebitda": ["ebitda", "adjusted ebitda"],
    "cash": ["cash and cash equivalents"],
    "total_debt": ["total debt", "long-term debt", "short-term borrowings"],
    "operating_cash_flow": ["cash flow from operations", "net cash provided by operating activities"],
    "capex": ["capital expenditures", "purchases of property and equipment"],
    "total_assets": ["total assets"],
    "total_liabilities": ["total liabilities"],
    "total_equity": ["total stockholders' equity", "total shareholders' equity"],
}


# ---------------------------------------------------------------------------
# APP-WIDE CONSTANTS
# ---------------------------------------------------------------------------

APP_NAME = "FinDoc AI"
APP_SUBTITLE = "AI Financial Statement Intelligence Platform"
SUPPORTED_FILE_TYPES = ["pdf"]
RECOMMENDATION_LABELS = ["BUY", "HOLD", "SELL"]


# ---------------------------------------------------------------------------
# SINGLETON CONFIG INSTANCES
# ---------------------------------------------------------------------------

llm_config = LLMConfig()
embedding_config = EmbeddingConfig()
chunking_config = ChunkingConfig()
vector_store_config = VectorStoreConfig()