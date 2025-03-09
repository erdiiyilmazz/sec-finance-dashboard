import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import os

from models.data_cache import DataCache, CacheEntry


class SECAPIService:
    """
    Service for interacting with the SEC EDGAR API.
    """
    
    # Base URLs for SEC EDGAR API
    COMPANY_TICKERS_URL = "https://www.sec.gov/include/ticker.txt"
    SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{}.json"
    COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"
    COMPANY_CONCEPT_URL = "https://data.sec.gov/api/xbrl/companyconcept/CIK{}/us-gaap/{}.json"
    
    def __init__(self, cache_dir: str = "cache", user_agent: Optional[str] = None):
        """
        Initialize the SEC API service.
        
        Args:
            cache_dir: Directory to store cache files
            user_agent: User agent string to use for requests (required by SEC)
        """
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize caches
        self.company_tickers_cache = DataCache(name="company_tickers", default_ttl=timedelta(days=7))
        self.submissions_cache = DataCache(name="submissions", default_ttl=timedelta(days=1))
        self.company_facts_cache = DataCache(name="company_facts", default_ttl=timedelta(days=1))
        self.company_concept_cache = DataCache(name="company_concept", default_ttl=timedelta(days=1))
        
        # Load caches from files if they exist
        self._load_caches()
        
        # Set up requests session with appropriate headers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent or "Financial Dashboard/1.0",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov"
        })
        
        # Log the User-Agent being used
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized SEC API service with User-Agent: {self.session.headers['User-Agent']}")
    
    def get_company_tickers(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get a mapping of CIK numbers to ticker symbols.
        
        Args:
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Dictionary containing company ticker data
        """
        cache_key = "company_tickers"
        
        # Check cache first
        if not force_refresh:
            cached_data = self.company_tickers_cache.get(cache_key)
            if cached_data:
                self.logger.info("Using cached company tickers data")
                return cached_data
        
        # Fetch from SEC API
        self.logger.info(f"Fetching company tickers from SEC API: {self.COMPANY_TICKERS_URL}")
        try:
            response = self.session.get(self.COMPANY_TICKERS_URL)
            self.logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Error response from SEC API: {response.text}")
                
            response.raise_for_status()
            
            # Process the response - ticker.txt is tab-delimited
            result = {}
            for line in response.text.strip().split('\n'):
                if line:
                    ticker, cik_str = line.strip().split('\t')
                    # Convert CIK to 10-digit format with leading zeros
                    cik = str(cik_str).zfill(10)
                    result[cik] = {
                        "ticker": ticker.upper(),
                        "title": "",  # Title not available in ticker.txt
                        "cik": cik
                    }
            
            self.logger.info(f"Successfully fetched {len(result)} company tickers")
            
            # Cache the result
            self.company_tickers_cache.set(cache_key, result)
            self._save_caches()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching company tickers: {str(e)}")
            return {}
    
    def get_company_submissions(self, cik: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get submission history for a company.
        
        Args:
            cik: CIK number of the company
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Dictionary containing submission history
        """
        # Standardize CIK format
        if cik.isdigit():
            cik = cik.zfill(10)
        
        cache_key = f"submissions_{cik}"
        
        # Check cache first
        if not force_refresh:
            cached_data = self.submissions_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Using cached submissions data for CIK {cik}")
                return cached_data
        
        # Fetch from SEC API
        url = self.SUBMISSIONS_URL.format(cik)
        self.logger.info(f"Fetching submissions for CIK {cik} from SEC API: {url}")
        
        # Respect SEC rate limits (10 requests per second)
        time.sleep(0.1)
        
        try:
            response = self.session.get(url)
            self.logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Error response from SEC API: {response.text}")
                
            response.raise_for_status()
            
            # Process the response
            data = response.json()
            
            # Cache the result
            self.submissions_cache.set(cache_key, data)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched submissions for CIK {cik}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching submissions for CIK {cik}: {str(e)}")
            # Return empty dict if there was an error
            return {}
    
    def get_company_facts(self, cik: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get all XBRL facts for a company.
        
        Args:
            cik: CIK number of the company
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Dictionary containing all XBRL facts
        """
        # Standardize CIK format
        if cik.isdigit():
            cik = cik.zfill(10)
        
        cache_key = f"facts_{cik}"
        
        # Check cache first
        if not force_refresh:
            cached_data = self.company_facts_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Using cached company facts for CIK {cik}")
                return cached_data
        
        # Fetch from SEC API
        url = self.COMPANY_FACTS_URL.format(cik)
        self.logger.info(f"Fetching company facts for CIK {cik} from SEC API: {url}")
        
        # Respect SEC rate limits (10 requests per second)
        time.sleep(0.1)
        
        try:
            response = self.session.get(url)
            self.logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Error response from SEC API: {response.text}")
                
            response.raise_for_status()
            
            # Process the response
            data = response.json()
            
            # Cache the result
            self.company_facts_cache.set(cache_key, data)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched company facts for CIK {cik}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching company facts for CIK {cik}: {str(e)}")
            # Return empty dict if there was an error
            return {}
    
    def get_company_concept(self, cik: str, concept: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get a specific XBRL concept for a company.
        
        Args:
            cik: CIK number of the company
            concept: XBRL concept name (e.g., "Revenue", "NetIncomeLoss")
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Dictionary containing the concept data
        """
        # Standardize CIK format
        if cik.isdigit():
            cik = cik.zfill(10)
        
        cache_key = f"concept_{cik}_{concept}"
        
        # Check cache first
        if not force_refresh:
            cached_data = self.company_concept_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Using cached concept {concept} for CIK {cik}")
                return cached_data
        
        # Fetch from SEC API
        url = self.COMPANY_CONCEPT_URL.format(cik, concept)
        self.logger.info(f"Fetching concept {concept} for CIK {cik} from SEC API: {url}")
        
        # Respect SEC rate limits (10 requests per second)
        time.sleep(0.1)
        
        try:
            response = self.session.get(url)
            self.logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Error response from SEC API: {response.text}")
                
            response.raise_for_status()
            
            # Process the response
            data = response.json()
            
            # Cache the result
            self.company_concept_cache.set(cache_key, data)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched concept {concept} for CIK {cik}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching concept {concept} for CIK {cik}: {str(e)}")
            # Return empty dict if there was an error
            return {}
    
    def _load_caches(self) -> None:
        """Load caches from files."""
        # Company tickers cache
        tickers_cache_path = os.path.join(self.cache_dir, "company_tickers_cache.json")
        if os.path.exists(tickers_cache_path):
            self.company_tickers_cache = DataCache.load_from_file(tickers_cache_path)
        
        # Submissions cache
        submissions_cache_path = os.path.join(self.cache_dir, "submissions_cache.json")
        if os.path.exists(submissions_cache_path):
            self.submissions_cache = DataCache.load_from_file(submissions_cache_path)
        
        # Company facts cache
        facts_cache_path = os.path.join(self.cache_dir, "company_facts_cache.json")
        if os.path.exists(facts_cache_path):
            self.company_facts_cache = DataCache.load_from_file(facts_cache_path)
        
        # Company concept cache
        concept_cache_path = os.path.join(self.cache_dir, "company_concept_cache.json")
        if os.path.exists(concept_cache_path):
            self.company_concept_cache = DataCache.load_from_file(concept_cache_path)
    
    def _save_caches(self) -> None:
        """Save caches to files."""
        # Company tickers cache
        tickers_cache_path = os.path.join(self.cache_dir, "company_tickers_cache.json")
        self.company_tickers_cache.save_to_file(tickers_cache_path)
        
        # Submissions cache
        submissions_cache_path = os.path.join(self.cache_dir, "submissions_cache.json")
        self.submissions_cache.save_to_file(submissions_cache_path)
        
        # Company facts cache
        facts_cache_path = os.path.join(self.cache_dir, "company_facts_cache.json")
        self.company_facts_cache.save_to_file(facts_cache_path)
        
        # Company concept cache
        concept_cache_path = os.path.join(self.cache_dir, "company_concept_cache.json")
        self.company_concept_cache.save_to_file(concept_cache_path) 