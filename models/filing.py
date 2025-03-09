from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Filing:
    """
    Represents an SEC filing document.
    """
    accession_number: str
    form_type: str  # 10-K, 10-Q, 8-K, etc.
    filing_date: datetime
    period_end_date: datetime
    company_id: Optional[str] = None  # Reference to Company
    company: Optional["Company"] = None  # Back-reference to Company
    
    # Filing metadata
    url: Optional[str] = None
    is_amended: bool = False
    is_processed: bool = False
    processed_date: Optional[datetime] = None
    
    # Raw and processed data
    raw_data: Dict[str, Any] = field(default_factory=dict)
    extracted_metrics: List["FinancialMetric"] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate data after initialization."""
        if isinstance(self.filing_date, str):
            self.filing_date = datetime.fromisoformat(self.filing_date)
        if isinstance(self.period_end_date, str):
            self.period_end_date = datetime.fromisoformat(self.period_end_date)
    
    def add_metric(self, metric: "FinancialMetric") -> None:
        """Add an extracted financial metric from this filing."""
        self.extracted_metrics.append(metric)
        metric.filing = self
        
        # Also add to company if available
        if self.company:
            self.company.add_metric(metric)
    
    def get_fiscal_year(self) -> Optional[int]:
        """Get the fiscal year of this filing."""
        if not self.period_end_date:
            return None
        return self.period_end_date.year
    
    def get_fiscal_quarter(self) -> Optional[int]:
        """Get the fiscal quarter of this filing (for quarterly reports)."""
        if not self.period_end_date or self.form_type != '10-Q':
            return None
        month = self.period_end_date.month
        if month in (1, 2, 3):
            return 1
        elif month in (4, 5, 6):
            return 2
        elif month in (7, 8, 9):
            return 3
        else:
            return 4 