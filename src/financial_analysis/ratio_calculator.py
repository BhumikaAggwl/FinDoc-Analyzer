"""
ratio_calculator.py

Calculates standard financial ratios from extracted metrics.
Returns None for any ratio whose required inputs are missing --
never fabricates or estimates values.
"""

from typing import Dict, Optional
from logger import get_logger

log = get_logger("ratio_calculator")


class RatioCalculator:
    def __init__(self, metrics: Dict[str, Optional[float]]):
        self.m = metrics

    def _safe_div(self, numerator, denominator) -> Optional[float]:
        if numerator is None or denominator is None or denominator == 0:
            return None
        return round(numerator / denominator, 4)

    def calculate_all(self) -> Dict[str, Optional[float]]:
        ratios = {
            "gross_margin": self._safe_div(self.m.get("gross_profit"), self.m.get("revenue")),
            "operating_margin": self._safe_div(self.m.get("operating_income"), self.m.get("revenue")),
            "net_margin": self._safe_div(self.m.get("net_income"), self.m.get("revenue")),
            "roe": self._safe_div(self.m.get("net_income"), self.m.get("total_equity")),
            "roa": self._safe_div(self.m.get("net_income"), self.m.get("total_assets")),
            "debt_to_equity": self._safe_div(self.m.get("total_debt"), self.m.get("total_equity")),
            "current_ratio": self._safe_div(self.m.get("total_assets"), self.m.get("total_liabilities")),
            "free_cash_flow": self._compute_fcf(),
            "asset_turnover": self._safe_div(self.m.get("revenue"), self.m.get("total_assets")),
        }

        computed = sum(1 for v in ratios.values() if v is not None)
        log.info(f"Calculated {computed}/{len(ratios)} ratios (rest missing due to incomplete extracted data)")
        return ratios

    def _compute_fcf(self) -> Optional[float]:
        ocf = self.m.get("operating_cash_flow")
        capex = self.m.get("capex")
        if ocf is None or capex is None:
            return None
        return round(ocf - capex, 2)