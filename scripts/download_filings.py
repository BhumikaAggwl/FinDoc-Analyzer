"""
download_filings.py
Permanent utility: downloads real SEC EDGAR filings (HTML) into data/uploads/.
Users can also manually upload their own PDFs -- both work via DocumentExtractor.
"""

import requests
from pathlib import Path

HEADERS = {"User-Agent": "FinDocAI Research Project contact@example.com"}
OUTPUT_DIR = Path("data/uploads")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILINGS = {
    "Apple_10K.htm": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
    "Microsoft_10K.htm": "https://www.sec.gov/Archives/edgar/data/789019/000156459023032450/msft-10k_20230630.htm",
    "Tesla_10K.htm": "https://www.sec.gov/Archives/edgar/data/1318605/000162828024002390/tsla-20231231.htm",
    "Amazon_10K.htm": "https://www.sec.gov/Archives/edgar/data/1018724/000101872424000008/amzn-20231231.htm",
    "Nvidia_10K.htm": "https://www.sec.gov/Archives/edgar/data/1045810/000104581024000029/nvda-20240128.htm",
    "Alphabet_10K.htm": "https://www.sec.gov/Archives/edgar/data/1652044/000165204424000022/goog-20231231.htm",
    "Meta_10K.htm": "https://www.sec.gov/Archives/edgar/data/1326801/000132680124000012/meta-20231231.htm",
    "Apple_10Q.htm": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000069/aapl-20240330.htm",
    "Microsoft_10Q.htm": "https://www.sec.gov/Archives/edgar/data/789019/000095017024026876/msft-20240331.htm",
}


def download():
    for filename, url in FILINGS.items():
        out_path = OUTPUT_DIR / filename
        print(f"Fetching {filename} ...")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            out_path.write_text(resp.text, encoding="utf-8")
            print(f"Saved: {out_path}")
        except Exception as e:
            print(f"Failed for {filename}: {e}")


if __name__ == "__main__":
    download()
