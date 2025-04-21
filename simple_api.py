from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import sys
import os

# Add /app to the Python path
sys.path.append('/app')

# Import functions from our get_companies.py script
from get_companies import get_ticker_cik_mappings, get_company_info, get_all_companies, get_company_10k_filings, get_company_facts

# Import the stock service
from services.stock_service import StockService

# Create a mock router for financial analysis
print("Using mock financial_analysis_router due to import issues")
financial_analysis_router = APIRouter(
    prefix="/financial-analysis",
    tags=["financial-analysis"],
    responses={404: {"description": "Not found"}},
)

@financial_analysis_router.get("/debug")
async def debug_endpoint():
    """
    Debug endpoint that always returns success to test API connectivity.
    """
    return {
        "status": "success",
        "message": "Financial analysis API is working (mock version)",
        "endpoints": [
            "/financial-analysis/ratios/{ticker}",
            "/financial-analysis/ratios/compare"
        ]
    }

@financial_analysis_router.get("/ratios/compare") 
async def compare_financial_ratios_mock(tickers: str):
    """Mock endpoint for comparing financial ratios"""
    ticker_list = [t.strip().upper() for t in tickers.split(",")]
    results = {}
    
    for ticker in ticker_list:
        results[ticker] = {
            "name": f"Company {ticker}",
            "ratios": {
                "liquidity_ratios": {
                    "current_ratio": {
                        "value": 1.07,
                        "description": "Current Ratio",
                        "year": 2023
                    }
                },
                "profitability_ratios": {
                    "return_on_equity": {
                        "value": 78.37,
                        "description": "Return on Equity",
                        "year": 2023
                    }
                }
            }
        }
    
    return {
        "comparison": results,
        "tickers": ticker_list
    }

@financial_analysis_router.get("/ratios/{ticker}")
async def get_financial_ratios_mock(ticker: str):
    """Mock endpoint for financial ratios"""
    return {
        "ticker": ticker,
        "name": f"Company {ticker}",
        "ratios": {
            "liquidity_ratios": {
                "current_ratio": {
                    "value": 1.07,
                    "description": "Measures a company's ability to pay short-term obligations",
                    "formula": "Current Assets / Current Liabilities",
                    "interpretation": {
                        "good": "> 1.5",
                        "concern": "< 1.0"
                    },
                    "year": 2023
                },
                "quick_ratio": {
                    "value": 0.88,
                    "description": "Measures a company's ability to pay short-term obligations with its most liquid assets",
                    "formula": "(Current Assets - Inventory) / Current Liabilities",
                    "interpretation": {
                        "good": "> 1.0",
                        "concern": "< 0.7"
                    },
                    "year": 2023
                }
            },
            "solvency_ratios": {
                "debt_to_equity": {
                    "value": 1.74,
                    "description": "Measures a company's financial leverage",
                    "formula": "Total Liabilities / Stockholders' Equity",
                    "interpretation": {
                        "good": "< 1.5",
                        "concern": "> 2.0"
                    },
                    "year": 2023
                }
            },
            "profitability_ratios": {
                "return_on_assets": {
                    "value": 28.31,
                    "description": "Measures how efficiently a company is using its assets to generate profit",
                    "formula": "(Net Income / Total Assets) * 100%",
                    "interpretation": {
                        "good": "> 5%",
                        "concern": "< 2%"
                    },
                    "year": 2023
                },
                "return_on_equity": {
                    "value": 78.37,
                    "description": "Measures how efficiently a company is using its equity to generate profit",
                    "formula": "(Net Income / Stockholders' Equity) * 100%",
                    "interpretation": {
                        "good": "> 15%",
                        "concern": "< 10%"
                    },
                    "year": 2023
                }
            }
        }
    }

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get server configuration from environment variables with defaults
HOST = os.environ.get("API_HOST", "0.0.0.0")
PORT = int(os.environ.get("API_PORT", "8002"))

# Create FastAPI app
app = FastAPI(title="Simple SEC API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include financial analysis router
app.include_router(financial_analysis_router)

# Initialize services
stock_service = StockService()

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Simple SEC API is running"}

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/companies/")
def read_companies(limit: int = 20):
    """Get a list of companies."""
    # Ensure limit is an integer
    try:
        limit_int = int(limit)
    except (ValueError, TypeError):
        limit_int = 20
    
    return get_all_companies(limit=limit_int)

@app.get("/companies/{ticker}")
def read_company(ticker: str):
    """Get information about a specific company."""
    result = get_company_info(ticker)
    if "error" in result:
        raise HTTPException(status_code=404, detail=f"Company with ticker {ticker} not found")
    return result

@app.get("/companies/{ticker}/10k")
def read_company_10k_filings(ticker: str, limit: int = 5):
    """Get 10-K filings for a specific company."""
    try:
        limit_int = int(limit)
    except (ValueError, TypeError):
        limit_int = 5
    
    result = get_company_10k_filings(ticker, limit=limit_int)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/companies/{ticker}/facts")
def read_company_facts(ticker: str):
    """Get financial facts for a specific company from the SEC's Company Facts API."""
    result = get_company_facts(ticker)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/cik-mappings/sync")
def sync_cik_mappings(force_refresh: bool = False):
    """Sync CIK-ticker mappings."""
    try:
        # Always try to get mappings, with force_refresh passed through
        mappings = get_ticker_cik_mappings(force_refresh=force_refresh)
        
        if not mappings:
            # If we got no mappings even after trying cached data,
            # this is a real error
            logger.warning("No CIK mappings available - API may be rate limited and no cache exists")
            raise HTTPException(status_code=500, detail="Failed to synchronize CIK-ticker mappings")
        
        logger.info(f"Successfully synchronized {len(mappings)} CIK-ticker mappings")
        return {"message": f"Successfully synchronized {len(mappings)} CIK-ticker mappings"}
    except Exception as e:
        logger.error(f"Error syncing CIK-ticker mappings: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to synchronize CIK-ticker mappings")

@app.post("/companies/{ticker}/sync")
def sync_company_data(ticker: str, force_refresh: bool = False):
    """Sync data for a specific company."""
    try:
        result = get_company_info(ticker)
        if "error" in result:
            raise HTTPException(status_code=404, detail=f"Failed to synchronize data for {ticker}")
        return result
    except Exception as e:
        logger.error(f"Error syncing company data for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to synchronize data for {ticker}")

@app.get("/companies/{ticker}/stock-prices")
def get_stock_prices(ticker: str, period: str = "1y", force_refresh: bool = False):
    """
    Get stock price data for a specific company.
    
    Args:
        ticker: The stock ticker symbol
        period: Time period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        force_refresh: Whether to force a refresh from the API
    """
    try:
        result = stock_service.get_stock_data(ticker, period, force_refresh)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return result
    except Exception as e:
        logger.error(f"Error fetching stock prices for {ticker}: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stock prices: {str(e)}")

if __name__ == "__main__":
    try:
        # Run the server with environment-based configuration
        uvicorn.run(
            app,
            host=HOST,
            port=PORT,
            reload=False,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1) 