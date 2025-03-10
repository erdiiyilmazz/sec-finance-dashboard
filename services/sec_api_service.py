import requests
import time
import logging
from typing import Dict, Optional, Any
from datetime import timedelta
import os

from models.data_cache import DataCache


class SECAPIService:
    """
    Service for interacting with the SEC EDGAR API.
    """
    
    # Base URLs for SEC EDGAR API
    COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
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
        
        # Use the provided user agent or get it from environment variables
        self.user_agent = user_agent or os.environ.get("SEC_API_USER_AGENT", "Financial Dashboard/1.0")
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Log the User-Agent being used
        self.logger.info(f"Initialized SEC API service with User-Agent: {self.user_agent}")
    
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
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate"
            }
            
            response = requests.get(self.COMPANY_TICKERS_URL, headers=headers)
            self.logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Error response from SEC API: {response.text}")
                
            response.raise_for_status()
            
            # Process the response - company_tickers.json is a JSON file
            data = response.json()
            result = {}
            
            # The data is in the format {"0": {"cik_str": "...", "ticker": "...", "title": "..."}, "1": {...}}
            for _, company_info in data.items():
                cik = str(company_info.get("cik_str", "")).zfill(10)
                ticker = company_info.get("ticker", "").upper()
                title = company_info.get("title", "")
                
                if cik and ticker:
                    result[ticker] = {
                        "ticker": ticker,
                        "title": title,
                        "cik": cik
                    }
            
            self.logger.info(f"Successfully fetched {len(result)} company tickers")
            
            # Cache the result
            self.company_tickers_cache.set(cache_key, result)
            self._save_caches()
            
            return result
        except Exception as e:
            self.logger.error(f"Error fetching company tickers: {e}")
            # Return empty dict on error
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
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }
            
            response = requests.get(url, headers=headers)
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
            self.logger.error(f"Error fetching submissions for CIK {cik}: {e}")
            # Return empty dict on error
            return {}
    
    def get_company_facts(self, cik: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get company facts for a company.
        
        Args:
            cik: CIK number of the company
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Dictionary containing company facts
        """
        # Standardize CIK format
        if cik.isdigit():
            cik = cik.zfill(10)
        
        cache_key = f"facts_{cik}"
        
        # Check cache first
        if not force_refresh:
            cached_data = self.company_facts_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Using cached company facts data for CIK {cik}")
                return cached_data
        
        # Fetch from SEC API
        url = self.COMPANY_FACTS_URL.format(cik)
        self.logger.info(f"Fetching company facts for CIK {cik} from SEC API: {url}")
        
        # Respect SEC rate limits (10 requests per second)
        time.sleep(0.1)
        
        try:
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }
            
            response = requests.get(url, headers=headers)
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
            self.logger.error(f"Error fetching company facts for CIK {cik}: {e}")
            # Return empty dict on error
            return {}
    
    def get_company_concept(self, cik: str, concept: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get company concept data for a company.
        
        Args:
            cik: CIK number of the company
            concept: Concept to retrieve (e.g., "AccountsPayableCurrent")
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Dictionary containing company concept data
        """
        # Standardize CIK format
        if cik.isdigit():
            cik = cik.zfill(10)
        
        cache_key = f"concept_{cik}_{concept}"
        
        # Check cache first
        if not force_refresh:
            cached_data = self.company_concept_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Using cached company concept data for CIK {cik}, concept {concept}")
                return cached_data
        
        # Fetch from SEC API
        url = self.COMPANY_CONCEPT_URL.format(cik, concept)
        self.logger.info(f"Fetching company concept for CIK {cik}, concept {concept} from SEC API: {url}")
        
        # Respect SEC rate limits (10 requests per second)
        time.sleep(0.1)
        
        try:
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }
            
            response = requests.get(url, headers=headers)
            self.logger.info(f"Response status code: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Error response from SEC API: {response.text}")
                
            response.raise_for_status()
            
            # Process the response
            data = response.json()
            
            # Cache the result
            self.company_concept_cache.set(cache_key, data)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched company concept for CIK {cik}, concept {concept}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching company concept for CIK {cik}, concept {concept}: {e}")
            # Return empty dict on error
            return {}
    
    def _load_caches(self) -> None:
        """Load caches from files."""
        try:
            # Load company tickers cache
            cache_file = os.path.join(self.cache_dir, "company_tickers.json")
            if os.path.exists(cache_file):
                self.company_tickers_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded company tickers cache with {len(self.company_tickers_cache.entries)} entries")
            
            # Load submissions cache
            cache_file = os.path.join(self.cache_dir, "submissions.json")
            if os.path.exists(cache_file):
                self.submissions_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded submissions cache with {len(self.submissions_cache.entries)} entries")
            
            # Load company facts cache
            cache_file = os.path.join(self.cache_dir, "company_facts.json")
            if os.path.exists(cache_file):
                self.company_facts_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded company facts cache with {len(self.company_facts_cache.entries)} entries")
            
            # Load company concept cache
            cache_file = os.path.join(self.cache_dir, "company_concept.json")
            if os.path.exists(cache_file):
                self.company_concept_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded company concept cache with {len(self.company_concept_cache.entries)} entries")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error loading caches: {e}")
    
    def _save_caches(self) -> None:
        """Save caches to files."""
        try:
            # Save company tickers cache
            cache_file = os.path.join(self.cache_dir, "company_tickers.json")
            self.company_tickers_cache.save_to_file(cache_file)
            
            # Save submissions cache
            cache_file = os.path.join(self.cache_dir, "submissions.json")
            self.submissions_cache.save_to_file(cache_file)
            
            # Save company facts cache
            cache_file = os.path.join(self.cache_dir, "company_facts.json")
            self.company_facts_cache.save_to_file(cache_file)
            
            # Save company concept cache
            cache_file = os.path.join(self.cache_dir, "company_concept.json")
            self.company_concept_cache.save_to_file(cache_file)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error saving caches: {e}") 