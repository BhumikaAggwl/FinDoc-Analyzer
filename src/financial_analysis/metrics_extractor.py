"""
metrics_extractor.py

Extracts key financial metrics (Revenue, Net Income, EPS, etc.) from
document text using pattern matching against known line-item aliases.
"""

import re
from typing import Dict, Optional, List
from config import FINANCIAL_METRIC_ALIASES
from logger import get_logger

log = get_logger("metrics_extractor")

# Matches numbers like: $383,285, 383,285 million, (1,234), 3.5%, $6.13
NUMBER_PATTERN = r"\$?\(?-?[\d,]+\.?\d*\)?%?"


class MetricsExtractor:
    def __init__(self):
        self.aliases = FINANCIAL_METRIC_ALIASES

    def extract_metrics(self, full_text: str) -> Dict[str, Optional[float]]:
        """
        Scans document text for known financial line items and extracts
        the first plausible numeric value found near each alias.
        """
        results = {}
        text_lower = full_text.lower()

        for metric_key, aliases in self.aliases.items():
            value = self._find_metric_value(text_lower, full_text, aliases)
            results[metric_key] = value

        log.info(f"Extracted {sum(1 for v in results.values() if v is not None)}/{len(results)} metrics")
        return results

    def _find_metric_value(self, text_lower: str, original_text: str, aliases: List[str]) -> Optional[float]:
        for alias in aliases:
            idx = text_lower.find(alias.lower())
            if idx == -1:
                continue

            # Look at a window of text right after the alias mention
            window = original_text[idx: idx + 200]
            numbers = re.findall(NUMBER_PATTERN, window)

            for raw_num in numbers:
                parsed = self._parse_number(raw_num)
                if parsed is not None:
                    return parsed

        return None

    def _parse_number(self, raw: str) -> Optional[float]:
        cleaned = raw.replace("$", "").replace(",", "").replace("%", "")
        is_negative = cleaned.startswith("(") and cleaned.endswith(")")
        cleaned = cleaned.replace("(", "").replace(")", "")

        try:
            value = float(cleaned)
            return -value if is_negative else value
        except ValueError:
            return None