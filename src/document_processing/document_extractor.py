"""
document_extractor.py

Extracts structured text from financial documents in either PDF or HTML format.
This is the permanent entry point of the pipeline -- PDFs (user uploads) use
PyMuPDF; HTML (e.g. SEC EDGAR filings) use BeautifulSoup. Both return the same
standardized page-structured output so downstream modules (chunker, classifier)
don't need to know the source format.
"""

from pathlib import Path
from typing import List, Dict
import fitz  # PyMuPDF
from bs4 import BeautifulSoup

from logger import get_logger

log = get_logger("document_extractor")


class DocumentExtractor:
    """Extracts and structures text content from PDF or HTML financial documents."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        self.file_type = self.file_path.suffix.lower()

        if self.file_type not in [".pdf", ".htm", ".html"]:
            raise ValueError(f"Unsupported file type: {self.file_type}")

    def extract_pages(self) -> List[Dict]:
        """
        Returns standardized output regardless of source format:
        [{"page_number": 1, "text": "..."}, ...]

        For HTML (no real pages), the document is split into pseudo-pages
        of ~3000 characters so downstream chunking/citation logic still works.
        """
        if self.file_type == ".pdf":
            return self._extract_pdf()
        else:
            return self._extract_html()

    def _extract_pdf(self) -> List[Dict]:
        pages = []
        try:
            doc = fitz.open(self.file_path)
            log.info(f"Opened PDF: {self.file_path.name} ({doc.page_count} pages)")

            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                text = page.get_text("text").strip()
                if text:
                    pages.append({"page_number": page_num + 1, "text": text})

            doc.close()
            log.info(f"Extracted text from {len(pages)} non-empty PDF pages")
            return pages

        except Exception as e:
            log.error(f"Failed to extract PDF: {e}")
            raise

    def _extract_html(self) -> List[Dict]:
        try:
            html_content = self.file_path.read_text(encoding="utf-8", errors="ignore")
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove non-content and XBRL/hidden metadata elements
            for tag in soup(["script", "style", "head", "meta", "link", "ix:header", "ix:hidden"]):
                tag.decompose()

            # Remove elements explicitly marked hidden (common in XBRL-tagged filings)
            for tag in soup.find_all(style=lambda v: v and "display:none" in v.replace(" ", "")):
                tag.decompose()

            for tag in soup.find_all(attrs={"style": True}):
                style = tag.get("style", "").replace(" ", "")
                if "display:none" in style or "visibility:hidden" in style:
                    tag.decompose()

            full_text = soup.get_text(separator="\n")

            # Clean up: drop lines that are just XBRL member tags or ID-like noise
            lines = []
            for line in full_text.splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("aapl:", "us-gaap:", "srt:", "0000")):
                    continue
                if len(line) < 3:
                    continue
                lines.append(line)

            full_text = "\n".join(lines)

            log.info(f"Opened HTML: {self.file_path.name} ({len(full_text)} characters)")

            page_size = 3000
            pages = []
            for i in range(0, len(full_text), page_size):
                chunk_text = full_text[i:i + page_size]
                if chunk_text.strip():
                    pages.append({
                        "page_number": (i // page_size) + 1,
                        "text": chunk_text
                    })

            log.info(f"Extracted {len(pages)} pseudo-pages from HTML")
            return pages

        except Exception as e:
            log.error(f"Failed to extract HTML: {e}")
            raise
        
            
    def extract_full_text(self) -> str:
        pages = self.extract_pages()
        return "\n\n".join(p["text"] for p in pages)

    def get_metadata(self) -> Dict:
        if self.file_type == ".pdf":
            doc = fitz.open(self.file_path)
            metadata = {
                "file_name": self.file_path.name,
                "file_type": "pdf",
                "page_count": doc.page_count,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
            }
            doc.close()
            return metadata
        else:
            return {
                "file_name": self.file_path.name,
                "file_type": "html",
                "page_count": None,
                "title": "",
                "author": "",
            }