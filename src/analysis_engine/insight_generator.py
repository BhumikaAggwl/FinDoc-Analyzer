"""
insight_generator.py

Generates structured equity-research-style insights (Executive Summary,
Business Model, Risk Analysis, SWOT, etc.) by combining RAG-retrieved
narrative context with extracted financial metrics.
"""

import requests
from typing import Dict, Optional
from src.rag.retriever import Retriever
from config import llm_config
from logger import get_logger

log = get_logger("insight_generator")

SECTION_QUERIES = {
    "executive_summary": "Provide an overview of the company's overall performance, strategy, and outlook",
    "business_model": "Describe the company's business model, products, and revenue sources",
    "competitive_position": "Describe the company's competitive advantages and market position",
    "revenue_analysis": "Discuss revenue trends, drivers, and segment performance",
    "risk_analysis": "What are the company's main risk factors",
    "capital_allocation": "Discuss capital allocation, dividends, share buybacks, and acquisitions",
    "growth_strategy": "Describe the company's growth strategy and future plans",
    "management_commentary": "Summarize management's discussion and analysis of results",
}

ANALYST_SYSTEM_PROMPT = """You are a Senior Equity Research Analyst at a top-tier
global asset management firm. Write institutional-quality analysis based strictly
on the provided document context and financial metrics. Never use casual or
marketing language. Explain what happened, why it happened, why it matters for
investors, and what to monitor next. If context is insufficient, say so explicitly."""


class InsightGenerator:
    def __init__(self):
        self.retriever = Retriever()
        self.api_key = llm_config.groq_api_key
        self.model = llm_config.groq_model
        self.url = f"{llm_config.groq_base_url}/chat/completions"

    def generate_section(self, section_key: str, document_id: str,
                          metrics: Optional[Dict] = None) -> str:
        if section_key not in SECTION_QUERIES:
            raise ValueError(f"Unknown section: {section_key}")

        query = SECTION_QUERIES[section_key]
        context = self.retriever.build_context(query, document_id=document_id, top_k=5)

        metrics_str = ""
        if metrics:
            metrics_str = "\n".join(f"- {k}: {v}" for k, v in metrics.items() if v is not None)

        user_prompt = f"""SECTION: {section_key.replace('_', ' ').title()}

DOCUMENT CONTEXT:
{context}

EXTRACTED FINANCIAL METRICS:
{metrics_str if metrics_str else "No reliable metrics extracted."}

Write a concise analytical paragraph (3-5 sentences) for this section, citing page numbers where possible."""

        return self._call_llm(user_prompt)

    def generate_full_report(self, document_id: str, metrics: Optional[Dict] = None) -> Dict[str, str]:
        report = {}
        for section_key in SECTION_QUERIES:
            log.info(f"Generating section: {section_key}")
            report[section_key] = self.generate_section(section_key, document_id, metrics)
        return report

    def _call_llm(self, user_prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": llm_config.temperature,
            "max_tokens": llm_config.max_tokens,
        }
        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            log.error(f"LLM call failed: {e}")
            return f"Error generating insight: {e}"