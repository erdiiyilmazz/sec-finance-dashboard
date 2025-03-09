from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Company:
    """
    Represents a company in the S&P 500 index.
    """
    ticker: str
    name: str
    cik: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    founded_year: Optional[int] = None
    description: Optional[str] = None
    website: Optional[str] = None
    
    # Relationships
    filings: List["Filing"] = field(default_factory=list)
    metrics: Dict[str, "FinancialMetric"] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate and standardize data after initialization."""
        self.ticker = self.ticker.upper() if self.ticker else None
        
    def add_filing(self, filing: "Filing") -> None:
        """Add a filing to this company."""
        self.filings.append(filing)
        filing.company = self
    
    def get_latest_filing(self, form_type: str) -> Optional["Filing"]:
        """Get the most recent filing of a specific type."""
        relevant_filings = [f for f in self.filings if f.form_type == form_type]
        if not relevant_filings:
            return None
        return max(relevant_filings, key=lambda f: f.filing_date)
    
    def add_metric(self, metric: "FinancialMetric") -> None:
        """Add a financial metric to this company."""
        key = f"{metric.name}_{metric.period}_{metric.date.isoformat()}"
        self.metrics[key] = metric
        metric.company = self 