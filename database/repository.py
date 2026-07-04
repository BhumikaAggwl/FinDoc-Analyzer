"""
repository.py

Data access layer for the SQL database. Provides clean functions to
save and retrieve companies, filings, metrics, and ratios.
"""

from typing import Dict, Optional, List
from database.models import SessionLocal, Company, Filing, FinancialMetric, FinancialRatio
from logger import get_logger

log = get_logger("repository")


def get_or_create_company(name: str, ticker: Optional[str] = None) -> Company:
    session = SessionLocal()
    try:
        company = session.query(Company).filter_by(name=name).first()
        if not company:
            company = Company(name=name, ticker=ticker)
            session.add(company)
            session.commit()
            session.refresh(company)
            log.info(f"Created new company: {name}")
        return company
    finally:
        session.close()


def save_filing(document_id: str, file_name: str, company_name: str,
                 filing_type: str = None, ticker: str = None) -> int:
    session = SessionLocal()
    try:
        company = session.query(Company).filter_by(name=company_name).first()
        if not company:
            company = Company(name=company_name, ticker=ticker)
            session.add(company)
            session.commit()
            session.refresh(company)

        existing = session.query(Filing).filter_by(document_id=document_id).first()
        if existing:
            log.info(f"Filing '{document_id}' already exists, returning existing ID")
            return existing.id

        filing = Filing(
            document_id=document_id,
            file_name=file_name,
            filing_type=filing_type,
            company_id=company.id
        )
        session.add(filing)
        session.commit()
        session.refresh(filing)
        log.info(f"Saved filing: {document_id}")
        return filing.id
    finally:
        session.close()


def save_metrics(filing_id: int, metrics: Dict[str, Optional[float]]):
    session = SessionLocal()
    try:
        session.query(FinancialMetric).filter_by(filing_id=filing_id).delete()

        for name, value in metrics.items():
            metric = FinancialMetric(filing_id=filing_id, metric_name=name, metric_value=value)
            session.add(metric)

        session.commit()
        log.info(f"Saved {len(metrics)} metrics for filing_id={filing_id}")
    finally:
        session.close()


def save_ratios(filing_id: int, ratios: Dict[str, Optional[float]]):
    session = SessionLocal()
    try:
        session.query(FinancialRatio).filter_by(filing_id=filing_id).delete()

        for name, value in ratios.items():
            ratio = FinancialRatio(filing_id=filing_id, ratio_name=name, ratio_value=value)
            session.add(ratio)

        session.commit()
        log.info(f"Saved {len(ratios)} ratios for filing_id={filing_id}")
    finally:
        session.close()


def get_filing_metrics(document_id: str) -> Dict[str, Optional[float]]:
    session = SessionLocal()
    try:
        filing = session.query(Filing).filter_by(document_id=document_id).first()
        if not filing:
            return {}
        return {m.metric_name: m.metric_value for m in filing.metrics}
    finally:
        session.close()


def get_filing_ratios(document_id: str) -> Dict[str, Optional[float]]:
    session = SessionLocal()
    try:
        filing = session.query(Filing).filter_by(document_id=document_id).first()
        if not filing:
            return {}
        return {r.ratio_name: r.ratio_value for r in filing.ratios}
    finally:
        session.close()


def list_all_filings() -> List[Dict]:
    session = SessionLocal()
    try:
        filings = session.query(Filing).all()
        return [
            {
                "document_id": f.document_id,
                "file_name": f.file_name,
                "filing_type": f.filing_type,
                "company_name": f.company.name if f.company else None,
                "uploaded_at": f.uploaded_at,
            }
            for f in filings
        ]
    finally:
        session.close()