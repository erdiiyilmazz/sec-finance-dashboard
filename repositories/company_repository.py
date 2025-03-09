from typing import List, Optional, Dict, Any
import json
import os

from models.company import Company
from repositories.base_repository import BaseRepository


class CompanyRepository(BaseRepository[Company]):
    """
    Repository for managing Company entities.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the repository with a data directory."""
        self.data_dir = data_dir
        self.companies_file = os.path.join(data_dir, "companies.json")
        self.companies: Dict[str, Company] = {}
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load companies from file if it exists
        if os.path.exists(self.companies_file):
            self._load_from_file()
    
    def get_by_id(self, id: str) -> Optional[Company]:
        """Get a company by its ticker symbol."""
        return self.companies.get(id.upper())
    
    def get_by_ticker(self, ticker: str) -> Optional[Company]:
        """Get a company by its ticker symbol."""
        return self.companies.get(ticker.upper())
    
    def get_by_cik(self, cik: str) -> Optional[Company]:
        """Get a company by its CIK number."""
        for company in self.companies.values():
            if company.cik == cik:
                return company
        return None
    
    def get_all(self) -> List[Company]:
        """Get all companies."""
        return list(self.companies.values())
    
    def create(self, company: Company) -> Company:
        """Create a new company."""
        if company.ticker in self.companies:
            raise ValueError(f"Company with ticker {company.ticker} already exists")
        
        self.companies[company.ticker] = company
        self._save_to_file()
        return company
    
    def update(self, company: Company) -> Company:
        """Update an existing company."""
        if company.ticker not in self.companies:
            raise ValueError(f"Company with ticker {company.ticker} does not exist")
        
        self.companies[company.ticker] = company
        self._save_to_file()
        return company
    
    def delete(self, id: str) -> bool:
        """Delete a company by its ticker symbol."""
        if id.upper() in self.companies:
            del self.companies[id.upper()]
            self._save_to_file()
            return True
        return False
    
    def find_by(self, criteria: Dict[str, Any]) -> List[Company]:
        """Find companies matching the given criteria."""
        results = []
        
        for company in self.companies.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(company, key) or getattr(company, key) != value:
                    match = False
                    break
            
            if match:
                results.append(company)
        
        return results
    
    def find_by_sector(self, sector: str) -> List[Company]:
        """Find companies in a specific sector."""
        return [c for c in self.companies.values() if c.sector == sector]
    
    def find_by_industry(self, industry: str) -> List[Company]:
        """Find companies in a specific industry."""
        return [c for c in self.companies.values() if c.industry == industry]
    
    def _save_to_file(self) -> None:
        """Save companies to a JSON file."""
        data = {}
        
        for ticker, company in self.companies.items():
            company_data = {
                "ticker": company.ticker,
                "name": company.name,
                "cik": company.cik,
                "sector": company.sector,
                "industry": company.industry,
                "founded_year": company.founded_year,
                "description": company.description,
                "website": company.website
            }
            data[ticker] = company_data
        
        with open(self.companies_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_from_file(self) -> None:
        """Load companies from a JSON file."""
        with open(self.companies_file, 'r') as f:
            data = json.load(f)
        
        for ticker, company_data in data.items():
            company = Company(
                ticker=company_data["ticker"],
                name=company_data["name"],
                cik=company_data.get("cik"),
                sector=company_data.get("sector"),
                industry=company_data.get("industry"),
                founded_year=company_data.get("founded_year"),
                description=company_data.get("description"),
                website=company_data.get("website")
            )
            self.companies[ticker] = company 