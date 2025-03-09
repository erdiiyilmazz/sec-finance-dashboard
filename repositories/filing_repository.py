from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime

from models.filing import Filing
from repositories.base_repository import BaseRepository


class FilingRepository(BaseRepository[Filing]):
    """
    Repository for managing SEC filings.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the repository with a data directory."""
        self.data_dir = data_dir
        self.filings_dir = os.path.join(data_dir, "filings")
        self.filings: Dict[str, Filing] = {}  # accession_number -> Filing
        
        # Create directories if they don't exist
        os.makedirs(self.filings_dir, exist_ok=True)
        
        # Load filings from files
        self._load_filings()
    
    def get_by_id(self, id: str) -> Optional[Filing]:
        """Get a filing by its accession number."""
        return self.filings.get(id)
    
    def get_all(self) -> List[Filing]:
        """Get all filings."""
        return list(self.filings.values())
    
    def create(self, filing: Filing) -> Filing:
        """Create a new filing."""
        if filing.accession_number in self.filings:
            raise ValueError(f"Filing with accession number {filing.accession_number} already exists")
        
        self.filings[filing.accession_number] = filing
        self._save_filing(filing)
        return filing
    
    def update(self, filing: Filing) -> Filing:
        """Update an existing filing."""
        if filing.accession_number not in self.filings:
            raise ValueError(f"Filing with accession number {filing.accession_number} does not exist")
        
        self.filings[filing.accession_number] = filing
        self._save_filing(filing)
        return filing
    
    def delete(self, id: str) -> bool:
        """Delete a filing by its accession number."""
        if id in self.filings:
            filing = self.filings[id]
            del self.filings[id]
            
            # Delete the filing file
            filing_path = self._get_filing_path(id)
            if os.path.exists(filing_path):
                os.remove(filing_path)
            
            return True
        return False
    
    def find_by(self, criteria: Dict[str, Any]) -> List[Filing]:
        """Find filings matching the given criteria."""
        results = []
        
        for filing in self.filings.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(filing, key) or getattr(filing, key) != value:
                    match = False
                    break
            
            if match:
                results.append(filing)
        
        return results
    
    def find_by_company_id(self, company_id: str) -> List[Filing]:
        """Find filings for a specific company."""
        return [f for f in self.filings.values() if f.company_id == company_id]
    
    def find_by_form_type(self, form_type: str) -> List[Filing]:
        """Find filings of a specific form type."""
        return [f for f in self.filings.values() if f.form_type == form_type]
    
    def find_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Filing]:
        """Find filings within a date range."""
        return [
            f for f in self.filings.values() 
            if start_date <= f.filing_date <= end_date
        ]
    
    def _get_filing_path(self, accession_number: str) -> str:
        """Get the file path for a filing."""
        return os.path.join(self.filings_dir, f"{accession_number}.json")
    
    def _save_filing(self, filing: Filing) -> None:
        """Save a filing to a JSON file."""
        filing_data = {
            "accession_number": filing.accession_number,
            "form_type": filing.form_type,
            "filing_date": filing.filing_date.isoformat(),
            "period_end_date": filing.period_end_date.isoformat(),
            "company_id": filing.company_id,
            "url": filing.url,
            "is_amended": filing.is_amended,
            "is_processed": filing.is_processed,
            "processed_date": filing.processed_date.isoformat() if filing.processed_date else None,
            "raw_data": filing.raw_data
        }
        
        filing_path = self._get_filing_path(filing.accession_number)
        with open(filing_path, 'w') as f:
            json.dump(filing_data, f, indent=2)
    
    def _load_filings(self) -> None:
        """Load all filings from JSON files."""
        for filename in os.listdir(self.filings_dir):
            if filename.endswith('.json'):
                filing_path = os.path.join(self.filings_dir, filename)
                with open(filing_path, 'r') as f:
                    filing_data = json.load(f)
                
                # Convert ISO format date strings to datetime
                filing_date = datetime.fromisoformat(filing_data["filing_date"])
                period_end_date = datetime.fromisoformat(filing_data["period_end_date"])
                processed_date = None
                if filing_data.get("processed_date"):
                    processed_date = datetime.fromisoformat(filing_data["processed_date"])
                
                filing = Filing(
                    accession_number=filing_data["accession_number"],
                    form_type=filing_data["form_type"],
                    filing_date=filing_date,
                    period_end_date=period_end_date,
                    company_id=filing_data.get("company_id"),
                    url=filing_data.get("url"),
                    is_amended=filing_data.get("is_amended", False),
                    is_processed=filing_data.get("is_processed", False),
                    processed_date=processed_date,
                    raw_data=filing_data.get("raw_data", {})
                )
                
                self.filings[filing.accession_number] = filing 