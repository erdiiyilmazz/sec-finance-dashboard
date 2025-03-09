from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class CIKTickerMapping:
    """
    Represents a mapping between SEC CIK numbers and company tickers.
    This is a critical component for accurate data retrieval from SEC.
    """
    cik: str  # SEC's Central Index Key
    ticker: str  # Stock ticker symbol
    company_name: str  # Official company name as per SEC
    
    # Metadata
    exchange: Optional[str] = None  # NYSE, NASDAQ, etc.
    is_active: bool = True  # Whether this mapping is currently active
    last_updated: datetime = field(default_factory=datetime.now)
    
    # Additional identifiers
    sic_code: Optional[str] = None  # Standard Industrial Classification code
    irs_number: Optional[str] = None  # IRS number if available
    
    # Alternative names and tickers
    alternative_tickers: List[str] = field(default_factory=list)  # Historical or alternative tickers
    alternative_names: List[str] = field(default_factory=list)  # Alternative company names
    
    def __post_init__(self):
        """Validate and standardize data after initialization."""
        # Standardize CIK format (10 digits with leading zeros)
        self.cik = self.cik.zfill(10) if self.cik.isdigit() else self.cik
        
        # Standardize ticker
        self.ticker = self.ticker.upper() if self.ticker else None
    
    @property
    def sec_edgar_url(self) -> str:
        """Generate the URL to the company's SEC EDGAR page."""
        return f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={self.cik}&owner=exclude"
    
    @property
    def formatted_cik(self) -> str:
        """Return CIK in standard SEC format (with leading zeros)."""
        if self.cik.isdigit():
            return self.cik.zfill(10)
        return self.cik
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "cik": self.cik,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "exchange": self.exchange,
            "is_active": self.is_active,
            "last_updated": self.last_updated.isoformat(),
            "sic_code": self.sic_code,
            "irs_number": self.irs_number,
            "alternative_tickers": self.alternative_tickers,
            "alternative_names": self.alternative_names
        } 