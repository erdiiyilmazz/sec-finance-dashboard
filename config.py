"""
Configuration file for the SEC Finance Dashboard application.
Contains static URLs, file paths, and other configuration values.
"""
import os

# SEC API Base URLs
SEC_API_URLS = {
    "COMPANY_TICKERS": "https://www.sec.gov/files/company_tickers.json",
    "SUBMISSIONS": "https://data.sec.gov/submissions/CIK{}.json",
    "COMPANY_FACTS": "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json",
    "COMPANY_CONCEPT": "https://data.sec.gov/api/xbrl/companyconcept/CIK{}/us-gaap/{}.json"
}

# Cache Configuration
CACHE_CONFIG = {
    "DEFAULT_CACHE_DIR": "cache",
    "CACHE_FILES": {
        "COMPANY_TICKERS": "company_tickers.json",
        "SUBMISSIONS": "submissions.json",
        "COMPANY_FACTS": "company_facts.json",
        "COMPANY_CONCEPT": "company_concept.json"
    }
}

# API Configuration
API_CONFIG = {
    "DEFAULT_USER_AGENT": "Financial Dashboard/1.0",
    "RATE_LIMIT_DELAY": 0.1,  # seconds between API requests
    "HOST": "0.0.0.0",         # Bind to all interfaces
    "PORT": 8002,
    "TIMEOUT": 30,             # Seconds before timing out
    "MAX_RETRIES": 3,
    "RETRY_BACKOFF": 0.5       # Seconds to wait between retries
}

# Web Dashboard Configuration
WEB_CONFIG = {
    # Use environment variable or default to service name for Docker networking
    "API_URL": os.environ.get("API_URL", "http://finance-app:8002"),
    "PORT": 8080
}

# Cache TTL (Time To Live) in days
CACHE_TTL = {
    "COMPANY_TICKERS": 7,
    "SUBMISSIONS": 1,
    "COMPANY_FACTS": 1,
    "COMPANY_CONCEPT": 1
} 