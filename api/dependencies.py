from fastapi import Depends
from typing import Optional
import os

from repositories.company_repository import CompanyRepository
from repositories.filing_repository import FilingRepository
from repositories.financial_metric_repository import FinancialMetricRepository
from repositories.cik_ticker_repository import CIKTickerRepository
from services.sec_api_service import SECAPIService
from services.sec_data_processor import SECDataProcessor
from services.financial_analysis import FinancialAnalysisService


# Repositories
def get_company_repository() -> CompanyRepository:
    """Get the company repository."""
    return CompanyRepository()


def get_filing_repository() -> FilingRepository:
    """Get the filing repository."""
    return FilingRepository()


def get_financial_metric_repository() -> FinancialMetricRepository:
    """Get the financial metric repository."""
    return FinancialMetricRepository()


def get_cik_ticker_repository() -> CIKTickerRepository:
    """Get the CIK-ticker repository."""
    return CIKTickerRepository()


# Services
def get_sec_api_service(user_agent: Optional[str] = None) -> SECAPIService:
    """Get the SEC API service."""
    # SEC requires a User-Agent with contact information in a specific format:
    # Name of organization/individual (contact email, telephone)
    
    # Get user agent components from environment variables
    sec_api_name = os.environ.get("SEC_API_NAME", "SEC Dashboard")
    sec_api_email = os.environ.get("SEC_API_EMAIL", "contact@example.com")
    sec_api_phone = os.environ.get("SEC_API_PHONE", "")
    
    # Construct the default user agent
    default_user_agent = f"{sec_api_name} ({sec_api_email}, {sec_api_phone})"
    
    # Check for User-Agent in environment variables
    env_user_agent = os.environ.get("SEC_API_USER_AGENT")
    
    # Use the provided user_agent, or the environment variable, or the default
    final_user_agent = user_agent or env_user_agent or default_user_agent
    
    return SECAPIService(user_agent=final_user_agent)


def get_sec_data_processor(
    sec_api_service: SECAPIService = Depends(get_sec_api_service),
    company_repository: CompanyRepository = Depends(get_company_repository),
    filing_repository: FilingRepository = Depends(get_filing_repository),
    metric_repository: FinancialMetricRepository = Depends(get_financial_metric_repository),
    cik_ticker_repository: CIKTickerRepository = Depends(get_cik_ticker_repository)
) -> SECDataProcessor:
    """Get the SEC data processor."""
    return SECDataProcessor(
        sec_api_service=sec_api_service,
        company_repository=company_repository,
        filing_repository=filing_repository,
        metric_repository=metric_repository,
        cik_ticker_repository=cik_ticker_repository
    )


def get_financial_analysis_service(
    company_repository: CompanyRepository = Depends(get_company_repository),
    metric_repository: FinancialMetricRepository = Depends(get_financial_metric_repository)
) -> FinancialAnalysisService:
    """Get the financial analysis service."""
    return FinancialAnalysisService(
        company_repository=company_repository,
        metric_repository=metric_repository
    ) 