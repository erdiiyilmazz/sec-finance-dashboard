import requests
import time
import logging
from typing import Dict, Optional, Any, Tuple
from datetime import timedelta
import os
import random

from models.data_cache import DataCache
from config import SEC_API_URLS, CACHE_CONFIG, API_CONFIG, CACHE_TTL


class SECAPIService:
    """
    Service for interacting with the SEC EDGAR API.
    """
    
    def __init__(self, cache_dir: str = CACHE_CONFIG["DEFAULT_CACHE_DIR"], user_agent: Optional[str] = None):
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
        self.company_tickers_cache = DataCache(
            name="company_tickers", 
            default_ttl=timedelta(days=CACHE_TTL["COMPANY_TICKERS"])
        )
        self.submissions_cache = DataCache(
            name="submissions", 
            default_ttl=timedelta(days=CACHE_TTL["SUBMISSIONS"])
        )
        self.company_facts_cache = DataCache(
            name="company_facts", 
            default_ttl=timedelta(days=CACHE_TTL["COMPANY_FACTS"])
        )
        self.company_concept_cache = DataCache(
            name="company_concept", 
            default_ttl=timedelta(days=CACHE_TTL["COMPANY_CONCEPT"])
        )
        
        # Load caches from files if they exist
        self._load_caches()
        
        # Use the provided user agent or get it from environment variables
        self.user_agent = user_agent or os.environ.get("SEC_API_USER_AGENT", API_CONFIG["DEFAULT_USER_AGENT"])
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
        # Log the User-Agent being used
        self.logger.info(f"Initialized SEC API service with User-Agent: {self.user_agent}")
    
    def get_company_tickers(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Get all company tickers from the SEC API.
        
        Args:
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Dictionary mapping CIK to company info (name, ticker, etc.)
        """
        cache_key = "tickers"
        
        # Check cache first
        if not force_refresh:
            cached_data = self.company_tickers_cache.get(cache_key)
            if cached_data:
                self.logger.info("Using cached company tickers data")
                return cached_data
        
        # Fetch from SEC API
        self.logger.info(f"Fetching company tickers from SEC API: {SEC_API_URLS['COMPANY_TICKERS']}")
        
        try:
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov"
            }
            
            status_code, data = self._make_request(SEC_API_URLS["COMPANY_TICKERS"], headers)
            
            if status_code != 200 or data is None:
                self.logger.error(f"Failed to fetch company tickers data (status: {status_code})")
                # Try to return cached data even if force_refresh was true
                cached_data = self.company_tickers_cache.get(cache_key)
                if cached_data:
                    self.logger.info("Falling back to cached company tickers data")
                    return cached_data
                return {}
            
            # Process the response - company_tickers.json is a JSON file
            result = {}
            
            # The SEC API returns a dictionary with numeric keys
            for _, company_info in data.items():
                cik_str = str(company_info["cik_str"]).zfill(10)
                result[cik_str] = {
                    "cik": cik_str,
                    "name": company_info["title"],
                    "ticker": company_info["ticker"]
                }
            
            # Cache the result
            self.company_tickers_cache.set(cache_key, result)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched {len(result)} company tickers")
            return result
            
        except Exception as e:
            self.logger.error(f"Error fetching company tickers: {e}")
            # Try to return cached data even if force_refresh was true
            cached_data = self.company_tickers_cache.get(cache_key)
            if cached_data:
                self.logger.info("Falling back to cached company tickers data after error")
                return cached_data
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
        url = SEC_API_URLS["SUBMISSIONS"].format(cik)
        self.logger.info(f"Fetching submissions for CIK {cik} from SEC API: {url}")
        
        try:
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }
            
            status_code, data = self._make_request(url, headers)
            
            if status_code != 200 or data is None:
                self.logger.error(f"Failed to fetch submissions data (status: {status_code})")
                # Try to return cached data even if force_refresh was true
                cached_data = self.submissions_cache.get(cache_key)
                if cached_data:
                    self.logger.info(f"Falling back to cached submissions data for CIK {cik}")
                    return cached_data
                return {}
            
            # Cache the result
            self.submissions_cache.set(cache_key, data)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched submissions for CIK {cik}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching submissions for CIK {cik}: {e}")
            # Try to return cached data even if force_refresh was true
            cached_data = self.submissions_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Falling back to cached submissions data for CIK {cik} after error")
                return cached_data
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
        url = SEC_API_URLS["COMPANY_FACTS"].format(cik)
        self.logger.info(f"Fetching company facts for CIK {cik} from SEC API: {url}")
        
        try:
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }
            
            status_code, data = self._make_request(url, headers)
            
            if status_code != 200 or data is None:
                self.logger.error(f"Failed to fetch company facts data (status: {status_code})")
                # Try to return cached data even if force_refresh was true
                cached_data = self.company_facts_cache.get(cache_key)
                if cached_data:
                    self.logger.info(f"Falling back to cached company facts data for CIK {cik}")
                    return cached_data
                return {}
            
            # Cache the result
            self.company_facts_cache.set(cache_key, data)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched company facts for CIK {cik}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching company facts for CIK {cik}: {e}")
            # Try to return cached data even if force_refresh was true
            cached_data = self.company_facts_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Falling back to cached company facts data for CIK {cik} after error")
                return cached_data
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
        url = SEC_API_URLS["COMPANY_CONCEPT"].format(cik, concept)
        self.logger.info(f"Fetching company concept for CIK {cik}, concept {concept} from SEC API: {url}")
        
        try:
            # Create custom headers for this request
            headers = {
                "User-Agent": self.user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "data.sec.gov"
            }
            
            status_code, data = self._make_request(url, headers)
            
            if status_code != 200 or data is None:
                self.logger.error(f"Failed to fetch company concept data (status: {status_code})")
                # Try to return cached data even if force_refresh was true
                cached_data = self.company_concept_cache.get(cache_key)
                if cached_data:
                    self.logger.info(f"Falling back to cached company concept data for CIK {cik}, concept {concept}")
                    return cached_data
                return {}
            
            # Cache the result
            self.company_concept_cache.set(cache_key, data)
            self._save_caches()
            
            self.logger.info(f"Successfully fetched company concept for CIK {cik}, concept {concept}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error fetching company concept for CIK {cik}, concept {concept}: {e}")
            # Try to return cached data even if force_refresh was true
            cached_data = self.company_concept_cache.get(cache_key)
            if cached_data:
                self.logger.info(f"Falling back to cached company concept data for CIK {cik}, concept {concept} after error")
                return cached_data
            return {}
    
    def _load_caches(self) -> None:
        """Load caches from files."""
        try:
            # Load company tickers cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["COMPANY_TICKERS"])
            if os.path.exists(cache_file):
                self.company_tickers_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded company tickers cache with {len(self.company_tickers_cache.entries)} entries")
            
            # Load submissions cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["SUBMISSIONS"])
            if os.path.exists(cache_file):
                self.submissions_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded submissions cache with {len(self.submissions_cache.entries)} entries")
            
            # Load company facts cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["COMPANY_FACTS"])
            if os.path.exists(cache_file):
                self.company_facts_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded company facts cache with {len(self.company_facts_cache.entries)} entries")
            
            # Load company concept cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["COMPANY_CONCEPT"])
            if os.path.exists(cache_file):
                self.company_concept_cache = DataCache.load_from_file(cache_file)
                logging.getLogger(__name__).info(f"Loaded company concept cache with {len(self.company_concept_cache.entries)} entries")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error loading caches: {e}")
    
    def _save_caches(self) -> None:
        """Save caches to files."""
        try:
            # Save company tickers cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["COMPANY_TICKERS"])
            self.company_tickers_cache.save_to_file(cache_file)
            
            # Save submissions cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["SUBMISSIONS"])
            self.submissions_cache.save_to_file(cache_file)
            
            # Save company facts cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["COMPANY_FACTS"])
            self.company_facts_cache.save_to_file(cache_file)
            
            # Save company concept cache
            cache_file = os.path.join(self.cache_dir, CACHE_CONFIG["CACHE_FILES"]["COMPANY_CONCEPT"])
            self.company_concept_cache.save_to_file(cache_file)
        except Exception as e:
            logging.getLogger(__name__).error(f"Error saving caches: {e}")

    def _make_request(self, url: str, headers: Dict[str, str] = None, max_retries: int = None) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        Make an HTTP request to the SEC API with retry logic and exponential backoff.
        
        Args:
            url: The URL to request
            headers: Headers to include in the request
            max_retries: Maximum number of retry attempts (defaults to API_CONFIG["MAX_RETRIES"])
            
        Returns:
            Tuple of (status_code, response_data)
        """
        if max_retries is None:
            max_retries = API_CONFIG["MAX_RETRIES"]
            
        if headers is None:
            headers = {}
            
        # Ensure User-Agent is set (required by SEC)
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.user_agent
            
        retries = 0
        while retries <= max_retries:
            try:
                # Add a small random delay to avoid hitting rate limits
                if retries > 0:
                    # Exponential backoff: wait longer after each retry
                    delay = (API_CONFIG["BACKOFF_FACTOR"] ** retries) + random.random()
                    self.logger.info(f"Retrying request to {url} in {delay:.2f} seconds (attempt {retries}/{max_retries})")
                    time.sleep(delay)
                else:
                    # Small delay even on first request to respect rate limits
                    time.sleep(API_CONFIG["RATE_LIMIT_DELAY"])
                
                response = requests.get(url, headers=headers)
                self.logger.info(f"Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    # Success
                    return response.status_code, response.json()
                elif response.status_code in (429, 403):
                    # Rate limited or forbidden (often due to rate limiting), retry after backoff
                    self.logger.warning(f"Rate limit exceeded for {url}, retrying after backoff")
                    retries += 1
                    if retries > max_retries:
                        self.logger.error(f"Error response from SEC API: {response.text}")
                        return response.status_code, None
                else:
                    # Other error
                    self.logger.error(f"Error response from SEC API: {response.text}")
                    return response.status_code, None
                    
            except Exception as e:
                self.logger.error(f"Error in request to {url}: {e}")
                retries += 1
                if retries > max_retries:
                    return 0, None
        
        return 0, None 