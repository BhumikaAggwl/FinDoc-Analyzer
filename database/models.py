"""
models.py

SQLAlchemy ORM models for storing structured financial data:
companies, filings, extracted metrics, and computed ratios.
Uses SQLite for zero-setup local storage.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from config import DATA_DIR

Base = declarative_base()

DB_PATH = DATA_DIR / "findoc.db"
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)
SessionLocal = sessionmaker(bind=engine)


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    ticker = Column(String, nullable=True)

    filings = relationship("Filing", back_populates="company")


class Filing(Base):
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True)
    document_id = Column(String, unique=True, nullable=False)  # e.g. "Apple_10K"
    filing_type = Column(String, nullable=True)  # "10-K", "10-Q", etc.
    file_name = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    company_id = Column(Integer, ForeignKey("companies.id"))
    company = relationship("Company", back_populates="filings")

    metrics = relationship("FinancialMetric", back_populates="filing")
    ratios = relationship("FinancialRatio", back_populates="filing")


class FinancialMetric(Base):
    __tablename__ = "financial_metrics"

    id = Column(Integer, primary_key=True)
    filing_id = Column(Integer, ForeignKey("filings.id"))
    metric_name = Column(String, nullable=False)
    metric_value = Column(Float, nullable=True)

    filing = relationship("Filing", back_populates="metrics")


class FinancialRatio(Base):
    __tablename__ = "financial_ratios"

    id = Column(Integer, primary_key=True)
    filing_id = Column(Integer, ForeignKey("filings.id"))
    ratio_name = Column(String, nullable=False)
    ratio_value = Column(Float, nullable=True)

    filing = relationship("Filing", back_populates="ratios")


def init_db():
    Base.metadata.create_all(engine)