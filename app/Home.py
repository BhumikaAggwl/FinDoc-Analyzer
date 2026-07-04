"""
Home.py
Chatbot-first Streamlit demo for FinDoc AI.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from database.models import init_db
from database.repository import list_all_filings, get_filing_metrics, get_filing_ratios
from src.rag.rag_pipeline import RAGPipeline
from src.analysis_engine.investment_recommender import InvestmentRecommender
from config import APP_NAME, APP_SUBTITLE

st.set_page_config(page_title=APP_NAME, page_icon="📊", layout="wide")
init_db()

st.title(f"📊 {APP_NAME}")
st.caption(APP_SUBTITLE)

filings = list_all_filings()
if not filings:
    st.warning("No filings found. Run `python -m scripts.ingest_all` first.")
    st.stop()

doc_map = {f"{f['company_name']} ({f['filing_type']})": f["document_id"] for f in filings}
document_id = doc_map[st.selectbox("Filing", list(doc_map.keys()), label_visibility="collapsed")]

st.markdown(
    """
    <style>
    .stChatInput textarea { font-size: 18px !important; padding: 14px !important; }
    .stChatInput { max-width: 900px; margin: 0 auto; }
    </style>
    """,
    unsafe_allow_html=True
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if question := st.chat_input("Ask about this filing..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.spinner("Analyzing..."):
        pipeline = RAGPipeline()
        result = pipeline.answer(question, document_id=document_id, top_k=5)
    st.session_state.messages.append({
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"]
    })

for msg in reversed(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            st.caption(f"Sources: pages {msg['sources']}")

with st.sidebar:
    st.caption("Metrics")
    metrics = get_filing_metrics(document_id)
    for k, v in metrics.items():
        if v is not None:
            st.text(f"{k.replace('_',' ')}: {v:,.1f}")

    st.divider()
    st.caption("Ratios")
    ratios = get_filing_ratios(document_id)
    for k, v in ratios.items():
        if v is not None:
            st.text(f"{k.replace('_',' ')}: {v:.3f}")

    st.divider()
    if st.button("Get recommendation", use_container_width=True):
        with st.spinner("..."):
            rec = InvestmentRecommender().recommend(document_id=document_id, ratios=ratios)
        color = {"BUY": "green", "HOLD": "orange", "SELL": "red"}.get(rec["recommendation"], "gray")
        st.markdown(f":{color}[**{rec['recommendation']}**] ({rec['confidence']}%)")
        st.caption(rec["rationale"])