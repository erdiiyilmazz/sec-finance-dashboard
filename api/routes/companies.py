from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

from models.financial_metric import MetricPeriod
from repositories.company_repository import CompanyRepository
from services.sec_data_processor import SECDataProcessor
from services.financial_analysis import FinancialAnalysisService
from api.dependencies import get_company_repository, get_sec_data_processor, get_financial_analysis_service


router = APIRouter(
    prefix="/companies",
    tags=["companies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[Dict[str, Any]])
async def get_companies(
    skip: int = 0,
    limit: int = 100,
    company_repo: CompanyRepository = Depends(get_company_repository)
):
    """
    Get a list of companies.
    """
    companies = company_repo.get_all()
    
    # Convert to dictionaries
    result = []
    for company in companies[skip:skip+limit]:
        result.append({
            "ticker": company.ticker,
            "name": company.name,
            "cik": company.cik,
            "sector": company.sector,
            "industry": company.industry
        })
    
    return result


@router.get("/{ticker}", response_model=Dict[str, Any])
async def get_company(
    ticker: str,
    company_repo: CompanyRepository = Depends(get_company_repository)
):
    """
    Get a company by ticker symbol.
    """
    company = company_repo.get_by_ticker(ticker)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")
    
    return {
        "ticker": company.ticker,
        "name": company.name,
        "cik": company.cik,
        "sector": company.sector,
        "industry": company.industry,
        "founded_year": company.founded_year,
        "description": company.description,
        "website": company.website
    }


@router.get("/{ticker}/metrics/{metric_name}", response_model=Dict[str, Any])
async def get_company_metric(
    ticker: str,
    metric_name: str,
    period: Optional[str] = Query("annual", description="Metric period (annual, quarterly, ttm, ytd)"),
    analysis_service: FinancialAnalysisService = Depends(get_financial_analysis_service)
):
    """
    Get a specific financial metric for a company.
    """
    # Convert period string to enum
    period_enum = MetricPeriod.ANNUAL
    if period == "quarterly":
        period_enum = MetricPeriod.QUARTERLY
    elif period == "ttm":
        period_enum = MetricPeriod.TTM
    elif period == "ytd":
        period_enum = MetricPeriod.YTD
    
    # Get time series data
    time_series = analysis_service.get_metric_time_series(ticker, metric_name, period_enum)
    
    if not time_series:
        raise HTTPException(
            status_code=404, 
            detail=f"No {metric_name} data found for {ticker} with period {period}"
        )
    
    # Calculate growth rates
    growth_rates = analysis_service.calculate_growth_rates(ticker, metric_name, period_enum)
    
    # Calculate CAGR (only for annual data)
    cagr = None
    if period_enum == MetricPeriod.ANNUAL:
        cagr = analysis_service.calculate_cagr(ticker, metric_name)
    
    # Format the response
    return {
        "ticker": ticker,
        "metric_name": metric_name,
        "period": period,
        "time_series": [
            {"date": date.isoformat(), "value": value}
            for date, value in time_series
        ],
        "growth_rates": [
            {"date": date.isoformat(), "rate": rate}
            for date, rate in growth_rates
        ],
        "cagr": cagr
    }


@router.get("/{ticker}/ratios", response_model=Dict[str, float])
async def get_company_ratios(
    ticker: str,
    analysis_service: FinancialAnalysisService = Depends(get_financial_analysis_service)
):
    """
    Get financial ratios for a company.
    """
    try:
        ratios = analysis_service.calculate_ratios(ticker)
        return ratios
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Error calculating ratios for {ticker}: {str(e)}")


@router.get("/{ticker}/10k", response_model=Dict[str, Any])
async def get_company_10k_filings(
    ticker: str,
    limit: int = Query(5, description="Number of 10-K filings to return"),
    company_repo: CompanyRepository = Depends(get_company_repository)
):
    """
    Get 10-K filings for a company.
    """
    try:
        # Get company info
        company = company_repo.get_by_ticker(ticker)
        if not company:
            raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")
        
        cik = company.cik
        if not cik:
            raise HTTPException(status_code=404, detail=f"CIK not found for {ticker}")
        
        # Format CIK with leading zeros
        cik_padded = str(cik).zfill(10)
        
        # Fetch submissions data from SEC
        import requests
        from datetime import datetime
        
        # Get user agent components from environment variables
        sec_api_name = os.environ.get("SEC_API_NAME", "SEC Dashboard")
        sec_api_email = os.environ.get("SEC_API_EMAIL", "contact@example.com")
        sec_api_phone = os.environ.get("SEC_API_PHONE", "")
        
        # Construct the user agent or use the environment variable if available
        user_agent = os.environ.get("SEC_API_USER_AGENT") or f"{sec_api_name} ({sec_api_email}, {sec_api_phone})"
        
        url = f"https://data.sec.gov/submissions/CIK{cik_padded}.json"
        headers = {
            "User-Agent": user_agent
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        # Extract filing information
        filings = []
        recent_filings = data.get("filings", {}).get("recent", {})
        
        if not recent_filings:
            return {"ticker": ticker, "name": company.name, "cik": cik, "filings": []}
        
        # Get the indices of 10-K filings
        form_types = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_documents = recent_filings.get("primaryDocument", [])
        file_numbers = recent_filings.get("fileNumber", [])
        
        # Find 10-K filings
        ten_k_indices = [i for i, form in enumerate(form_types) if form == "10-K"]
        
        # Get current date for validation
        current_date = datetime.now().date()
        
        # Extract 10-K filing information
        for idx in ten_k_indices[:limit]:  # Limit to the most recent 'limit' filings
            if idx < len(filing_dates) and idx < len(accession_numbers):
                try:
                    # Parse the filing date
                    filing_date = datetime.strptime(filing_dates[idx], "%Y-%m-%d").date()
                    
                    # Skip future filings
                    if filing_date > current_date:
                        print(f"Skipping future filing date: {filing_dates[idx]}")
                        continue
                    
                    # Format the accession number for the URL
                    acc_no = accession_numbers[idx].replace('-', '')
                    
                    # Primary document
                    primary_doc = primary_documents[idx] if idx < len(primary_documents) else ""
                    
                    # Create the SEC URLs - we'll prioritize the interactive viewer URL
                    # This is the most reliable way to view SEC filings as it uses their modern iXBRL viewer
                    sec_viewer_url = f"https://www.sec.gov/ix?doc=/Archives/edgar/data/{cik_padded}/{acc_no}/{primary_doc}"
                    
                    # Legacy URL - keep as a fallback but may not work for all filings
                    legacy_url = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{acc_no}/{primary_doc}"
                    
                    # Modern index URL that usually works even when specific document links fail
                    index_url = f"https://www.sec.gov/Archives/edgar/data/{cik_padded}/{acc_no}/index.htm"
                    
                    filing = {
                        "form": "10-K",
                        "filingDate": filing_dates[idx],
                        "accessionNumber": accession_numbers[idx],
                        "primaryDocument": primary_doc,
                        "fileNumber": file_numbers[idx] if idx < len(file_numbers) else "",
                        "edgarUrl": sec_viewer_url,  # Use the interactive viewer as the primary URL
                        "legacyUrl": legacy_url,
                        "indexUrl": index_url
                    }
                    filings.append(filing)
                except ValueError as e:
                    print(f"Error parsing filing date {filing_dates[idx]}: {e}")
                    continue
        
        if not filings:
            return {
                "ticker": ticker,
                "name": company.name,
                "cik": cik,
                "filings": [],
                "message": "No valid 10-K filings found. This could be because all available filings are dated in the future."
            }
        
        return {
            "ticker": ticker,
            "cik": cik,
            "name": company.name,
            "filings": filings
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching 10-K filings: {str(e)}")


@router.post("/{ticker}/sync", response_model=Dict[str, Any])
async def sync_company_data(
    ticker: str,
    force_refresh: bool = False,
    data_processor: SECDataProcessor = Depends(get_sec_data_processor)
):
    """
    Synchronize company data with the SEC API.
    """
    company = data_processor.sync_company_data(ticker, force_refresh)
    
    if not company:
        raise HTTPException(
            status_code=404, 
            detail=f"Failed to synchronize data for {ticker}"
        )
    
    return {
        "ticker": company.ticker,
        "name": company.name,
        "cik": company.cik,
        "status": "synchronized",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/compare/{metric_name}", response_model=Dict[str, Any])
async def compare_companies(
    metric_name: str,
    tickers: str = Query(..., description="Comma-separated list of ticker symbols"),
    analysis_service: FinancialAnalysisService = Depends(get_financial_analysis_service)
):
    """
    Compare multiple companies based on a specific metric.
    """
    ticker_list = [t.strip() for t in tickers.split(",")]
    
    comparison = analysis_service.compare_companies(ticker_list, metric_name)
    
    if not comparison:
        raise HTTPException(
            status_code=404, 
            detail=f"No comparison data found for {metric_name} across {tickers}"
        )
    
    # Format the response
    result = {}
    for ticker, data in comparison.items():
        result[ticker] = {
            "company_name": data["company_name"],
            "latest_value": data["latest_value"],
            "latest_date": data["latest_date"].isoformat() if data["latest_date"] else None,
            "growth_rate": data["growth_rate"],
            "cagr": data["cagr"],
            "time_series": [
                {"date": date.isoformat(), "value": value}
                for date, value in data["time_series"]
            ]
        }
    
    return result


# Add a new router for CIK-ticker mappings
cik_mappings_router = APIRouter(
    prefix="/cik-mappings",
    tags=["cik-mappings"],
    responses={404: {"description": "Not found"}},
)

@cik_mappings_router.post("/sync", response_model=Dict[str, Any])
async def sync_cik_ticker_mappings(
    force_refresh: bool = False,
    data_processor: SECDataProcessor = Depends(get_sec_data_processor)
):
    """
    Synchronize CIK-ticker mappings with the SEC API.
    """
    mappings = data_processor.sync_cik_ticker_mappings(force_refresh)
    
    if not mappings:
        raise HTTPException(
            status_code=500, 
            detail="Failed to synchronize CIK-ticker mappings"
        )
    
    return {
        "count": len(mappings),
        "status": "synchronized",
        "timestamp": datetime.now().isoformat()
    } 