"""
rag_pipeline.py

Combines retrieval (RAG) with Groq LLM generation to produce
institutional-style equity research answers grounded in retrieved
document evidence.
"""

import requests
from src.rag.retriever import Retriever
from config import llm_config
from logger import get_logger

log = get_logger("rag_pipeline")

ANALYST_SYSTEM_PROMPT = """You are a Senior Equity Research Analyst at a top-tier
global asset management firm. You analyze corporate financial documents (10-Ks,
10-Qs, annual reports) with the rigor and language of institutional research.

Rules:
- Base your answer ONLY on the provided document context. Do not use outside knowledge.
- If the context does not contain enough information to answer, explicitly say so.
- Never use casual or marketing language. Write like a professional sell-side analyst.
- Where possible, reference the page number(s) from the context that support your answer.
- Explain not just WHAT the fact is, but WHY it matters for investors, when the context allows.
- Avoid hallucinating numbers or facts not present in the context.
"""


class RAGPipeline:
    def __init__(self):
        self.retriever = Retriever()
        self.api_key = llm_config.groq_api_key
        self.model = llm_config.groq_model
        self.url = f"{llm_config.groq_base_url}/chat/completions"

        if not self.api_key:
            raise ValueError("GROQ_API_KEY not set in .env")

    def answer(self, question: str, document_id: str = None, top_k: int = 6) -> dict:
        """
        Returns: {"answer": str, "context_used": str, "sources": list}
        """
        context = self.retriever.build_context(question, document_id=document_id, top_k=top_k)

        if not context.strip():
            return {
                "answer": "No relevant information was found in the uploaded document for this question.",
                "context_used": "",
                "sources": []
            }

        user_prompt = f"""DOCUMENT CONTEXT:
{context}

QUESTION:
{question}

Provide a professional equity research style answer based strictly on the context above."""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
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
            data = response.json()
            answer_text = data["choices"][0]["message"]["content"]

            log.info(f"Generated answer for question: '{question[:60]}...'")

            return {
                "answer": answer_text,
                "context_used": context,
                "sources": self._extract_page_numbers(context)
            }

        except Exception as e:
            log.error(f"LLM generation failed: {e}")
            return {
                "answer": f"Error generating response: {e}",
                "context_used": context,
                "sources": []
            }

    def _extract_page_numbers(self, context: str) -> list:
        import re
        pages = re.findall(r"\[Page (\d+)\]", context)
        return sorted(set(int(p) for p in pages))