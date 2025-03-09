from dataclasses import dataclass
from typing import Optional, Any, Union
from datetime import datetime
from enum import Enum


class MetricPeriod(str, Enum):
    """Enumeration of financial reporting periods."""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    TTM = "trailing_twelve_months"  # Trailing Twelve Months
    YTD = "year_to_date"


@dataclass
class FinancialMetric:
    """
    Represents a financial metric extracted from SEC filings.
    """
    name: str  # e.g., "revenue", "net_income", "eps"
    value: Union[float, int]
    date: datetime  # The date this metric is associated with (usually period end date)
    period: MetricPeriod  # Annual, quarterly, TTM, etc.
    
    # Metadata
    unit: str = "USD"  # Currency or other unit
    decimals: Optional[int] = None  # Precision information
    
    # Source information
    filing_id: Optional[str] = None  # Reference to Filing
    filing: Optional["Filing"] = None  # Back-reference to Filing
    company_id: Optional[str] = None  # Reference to Company
    company: Optional["Company"] = None  # Back-reference to Company
    
    # XBRL metadata
    xbrl_tag: Optional[str] = None  # Original XBRL tag
    xbrl_context: Optional[str] = None  # XBRL context reference
    
    # Calculation and validation
    is_calculated: bool = False  # Whether this was calculated rather than directly extracted
    calculation_method: Optional[str] = None  # Description of calculation if applicable
    confidence_score: Optional[float] = None  # Confidence in the extraction (0-1)
    
    def __post_init__(self):
        """Validate data after initialization."""
        if isinstance(self.date, str):
            self.date = datetime.fromisoformat(self.date)
        
        # Ensure period is a MetricPeriod enum
        if isinstance(self.period, str):
            self.period = MetricPeriod(self.period)
    
    @property
    def fiscal_year(self) -> Optional[int]:
        """Get the fiscal year of this metric."""
        if not self.date:
            return None
        return self.date.year
    
    @property
    def fiscal_quarter(self) -> Optional[int]:
        """Get the fiscal quarter of this metric (for quarterly metrics)."""
        if not self.date or self.period != MetricPeriod.QUARTERLY:
            return None
        month = self.date.month
        if month in (1, 2, 3):
            return 1
        elif month in (4, 5, 6):
            return 2
        elif month in (7, 8, 9):
            return 3
        else:
            return 4
    
    def format_value(self, include_unit: bool = True) -> str:
        """Format the value with appropriate units and precision."""
        if self.decimals is not None:
            formatted = f"{self.value:.{self.decimals}f}"
        elif isinstance(self.value, int):
            formatted = f"{self.value:,d}"
        else:
            formatted = f"{self.value:,.2f}"
            
        if include_unit and self.unit:
            return f"{formatted} {self.unit}"
        return formatted 