"""
investment_recommender.py

Generates a concise BUY/HOLD/SELL recommendation with confidence score,
based on retrieved narrative context and available financial ratios.
"""

import requests
import re
from typing import Dict, Optional
from src.rag.retriever import Retriever
from config import llm_config
from logger import get_logger

log = get_logger("investment_recommender")

RECOMMENDER_SYSTEM_PROMPT = """You are a Senior Equity Research Analyst. Based ONLY
on the provided context and ratios, give a short, decisive investment recommendation.

Respond in EXACTLY this format, nothing else:

RECOMMENDATION: [BUY/HOLD/SELL]
CONFIDENCE: [0-100]%
RATIONALE: [2-3 sentence justification citing page numbers where possible]
"""


class InvestmentRecommender:
    def __init__(self):
        self.retriever = Retriever()
        self.api_key = llm_config.groq_api_key
        self.model = llm_config.groq_model
        self.url = f"{llm_config.groq_base_url}/chat/completions"

    def recommend(self, document_id: str, ratios: Optional[Dict] = None) -> Dict:
        query = "overall financial performance, growth outlook, and risks relevant to investment decision"
        context = self.retriever.build_context(query, document_id=document_id, top_k=5)

        ratios_str = ""
        if ratios:
            ratios_str = "\n".join(f"- {k}: {v}" for k, v in ratios.items() if v is not None)

        user_prompt = f"""CONTEXT:
{context}

FINANCIAL RATIOS:
{ratios_str if ratios_str else "No reliable ratios available."}

Give your recommendation in the required format."""

        raw_output = self._call_llm(user_prompt)
        return self._parse_output(raw_output)

    def _call_llm(self, user_prompt: str) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": RECOMMENDER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": llm_config.temperature,
            "max_tokens": 300,
        }
        response = requests.post(self.url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def _parse_output(self, raw: str) -> Dict:
        rec_match = re.search(r"RECOMMENDATION:\s*(BUY|HOLD|SELL)", raw, re.IGNORECASE)
        conf_match = re.search(r"CONFIDENCE:\s*(\d+)", raw)
        rationale_match = re.search(r"RATIONALE:\s*(.+)", raw, re.DOTALL)

        return {
            "recommendation": rec_match.group(1).upper() if rec_match else "HOLD",
            "confidence": int(conf_match.group(1)) if conf_match else None,
            "rationale": rationale_match.group(1).strip() if rationale_match else raw.strip(),
        }