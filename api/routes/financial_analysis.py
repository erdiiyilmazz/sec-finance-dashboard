"""
Financial Analysis API Routes

This module provides API endpoints for financial ratio analysis.
"""

from fastapi import APIRouter, HTTPException, Query
import logging
from typing import Optional
import traceback

from services.financial_analysis_helpers import calculate_all_ratios
from get_companies import get_company_facts, get_company_info

router = APIRouter(
    prefix="/financial-analysis",
    tags=["financial-analysis"],
    responses={404: {"description": "Not found"}},
)

logger = logging.getLogger(__name__)

@router.get("/debug")
async def debug_endpoint():
    """
    Debug endpoint that always returns success to test API connectivity.
    """
    logger.info("Debug endpoint called")
    return {
        "status": "success",
        "message": "Financial analysis API is working",
        "endpoints": [
            "/financial-analysis/ratios/{ticker}",
            "/financial-analysis/ratios/compare"
        ]
    }

@router.get("/ratios/compare")
async def compare_financial_ratios(
    tickers: str = Query(..., description="Comma-separated list of tickers to compare"),
    ratio_types: Optional[str] = Query(None, description="Comma-separated list of ratio types to include (liquidity_ratios, solvency_ratios, profitability_ratios, valuation_ratios)")
):
    """
    Compare financial ratios across multiple companies.
    
    Args:
        tickers: Comma-separated list of company ticker symbols
        ratio_types: Comma-separated list of ratio types to include
        
    Returns:
        Dictionary containing financial ratios for each company
    """
    try:
        # Parse tickers
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        # Parse ratio types if provided
        ratio_type_filters = None
        if ratio_types:
            ratio_type_filters = [r.strip() for r in ratio_types.split(",")]
        
        # Get ratios for each company
        results = {}
        for ticker in ticker_list:
            try:
                # Get company facts
                company_facts = get_company_facts(ticker)
                
                if "error" in company_facts:
                    logger.warning(f"No facts found for company {ticker}")
                    results[ticker] = {"error": f"No company facts found: {company_facts['error']}"}
                    continue
                
                # Calculate ratios
                all_ratios = calculate_all_ratios(company_facts)
                
                # Filter ratio types if needed
                if ratio_type_filters:
                    filtered_ratios = {k: v for k, v in all_ratios.items() if k in ratio_type_filters}
                    # Always include metadata
                    if "metadata" in all_ratios:
                        filtered_ratios["metadata"] = all_ratios["metadata"]
                    all_ratios = filtered_ratios
                
                # Get company info
                company_info = get_company_info(ticker)
                company_name = company_info.get("name", "")
                
                # Add to results
                results[ticker] = {
                    "name": company_name,
                    "ratios": all_ratios
                }
                
            except Exception as e:
                logger.error(f"Error calculating ratios for {ticker}: {str(e)}")
                logger.error(traceback.format_exc())
                results[ticker] = {"error": str(e)}
        
        return {
            "comparison": results,
            "tickers": ticker_list
        }
        
    except Exception as e:
        logger.error(f"Error comparing financial ratios: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error comparing financial ratios: {str(e)}")

@router.get("/ratios/{ticker}")
async def get_financial_ratios(
    ticker: str,
    include_price: Optional[bool] = Query(False, description="Include price-based ratios")
):
    """
    Get comprehensive financial ratios for a company.
    
    Args:
        ticker: The company ticker symbol
        include_price: Whether to include price-based ratios (P/E, etc.)
        
    Returns:
        Dictionary containing financial ratios
    """
    try:
        # Standardize ticker
        ticker = ticker.upper()
        
        # Get company facts
        company_facts = get_company_facts(ticker)
        
        if "error" in company_facts:
            raise HTTPException(status_code=404, detail=f"No facts found for company {ticker}: {company_facts['error']}")
        
        # Get current stock price if needed
        current_price = None
        if include_price:
            # This would typically come from a stock price API
            # For now, we'll leave it as None
            pass
        
        # Calculate all ratios
        ratios = calculate_all_ratios(company_facts, current_price)
        
        # Get company info
        company_info = get_company_info(ticker)
        
        # Add company info to response
        response = {
            "ticker": ticker,
            "name": company_info.get("name", ""),
            "ratios": ratios
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating financial ratios for {ticker}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error calculating financial ratios: {str(e)}") 