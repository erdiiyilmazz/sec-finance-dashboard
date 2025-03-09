from typing import List, Optional, Dict, Any
import json
import os
from datetime import datetime

from models.cik_ticker_mapping import CIKTickerMapping
from repositories.base_repository import BaseRepository


class CIKTickerRepository(BaseRepository[CIKTickerMapping]):
    """
    Repository for managing CIK-Ticker mappings.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the repository with a data directory."""
        self.data_dir = data_dir
        self.mappings_file = os.path.join(data_dir, "cik_ticker_mappings.json")
        self.mappings: Dict[str, CIKTickerMapping] = {}  # CIK -> Mapping
        self.ticker_to_cik: Dict[str, str] = {}  # Ticker -> CIK
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Load mappings from file if it exists
        if os.path.exists(self.mappings_file):
            self._load_from_file()
    
    def get_by_id(self, id: str) -> Optional[CIKTickerMapping]:
        """Get a mapping by its CIK."""
        return self.mappings.get(id)
    
    def get_by_cik(self, cik: str) -> Optional[CIKTickerMapping]:
        """Get a mapping by its CIK."""
        # Standardize CIK format
        if cik.isdigit():
            cik = cik.zfill(10)
        return self.mappings.get(cik)
    
    def get_by_ticker(self, ticker: str) -> Optional[CIKTickerMapping]:
        """Get a mapping by its ticker symbol."""
        ticker = ticker.upper()
        cik = self.ticker_to_cik.get(ticker)
        if cik:
            return self.mappings.get(cik)
        return None
    
    def get_all(self) -> List[CIKTickerMapping]:
        """Get all mappings."""
        return list(self.mappings.values())
    
    def create(self, mapping: CIKTickerMapping) -> CIKTickerMapping:
        """Create a new mapping."""
        if mapping.cik in self.mappings:
            raise ValueError(f"Mapping with CIK {mapping.cik} already exists")
        
        self.mappings[mapping.cik] = mapping
        self.ticker_to_cik[mapping.ticker.upper()] = mapping.cik
        self._save_to_file()
        return mapping
    
    def update(self, mapping: CIKTickerMapping) -> CIKTickerMapping:
        """Update an existing mapping."""
        if mapping.cik not in self.mappings:
            raise ValueError(f"Mapping with CIK {mapping.cik} does not exist")
        
        # Update ticker-to-CIK mapping if ticker has changed
        old_mapping = self.mappings[mapping.cik]
        if old_mapping.ticker != mapping.ticker:
            if old_mapping.ticker in self.ticker_to_cik:
                del self.ticker_to_cik[old_mapping.ticker]
            self.ticker_to_cik[mapping.ticker.upper()] = mapping.cik
        
        self.mappings[mapping.cik] = mapping
        self._save_to_file()
        return mapping
    
    def delete(self, id: str) -> bool:
        """Delete a mapping by its CIK."""
        if id in self.mappings:
            mapping = self.mappings[id]
            del self.mappings[id]
            if mapping.ticker in self.ticker_to_cik:
                del self.ticker_to_cik[mapping.ticker]
            self._save_to_file()
            return True
        return False
    
    def find_by(self, criteria: Dict[str, Any]) -> List[CIKTickerMapping]:
        """Find mappings matching the given criteria."""
        results = []
        
        for mapping in self.mappings.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(mapping, key) or getattr(mapping, key) != value:
                    match = False
                    break
            
            if match:
                results.append(mapping)
        
        return results
    
    def find_by_exchange(self, exchange: str) -> List[CIKTickerMapping]:
        """Find mappings for a specific exchange."""
        return [m for m in self.mappings.values() if m.exchange == exchange]
    
    def _save_to_file(self) -> None:
        """Save mappings to a JSON file."""
        data = {}
        
        for cik, mapping in self.mappings.items():
            mapping_data = mapping.to_dict()
            data[cik] = mapping_data
        
        with open(self.mappings_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_from_file(self) -> None:
        """Load mappings from a JSON file."""
        with open(self.mappings_file, 'r') as f:
            data = json.load(f)
        
        for cik, mapping_data in data.items():
            # Convert ISO format date string to datetime
            last_updated = datetime.fromisoformat(mapping_data["last_updated"])
            
            mapping = CIKTickerMapping(
                cik=mapping_data["cik"],
                ticker=mapping_data["ticker"],
                company_name=mapping_data["company_name"],
                exchange=mapping_data.get("exchange"),
                is_active=mapping_data.get("is_active", True),
                last_updated=last_updated,
                sic_code=mapping_data.get("sic_code"),
                irs_number=mapping_data.get("irs_number"),
                alternative_tickers=mapping_data.get("alternative_tickers", []),
                alternative_names=mapping_data.get("alternative_names", [])
            )
            
            self.mappings[cik] = mapping
            self.ticker_to_cik[mapping.ticker.upper()] = cik 