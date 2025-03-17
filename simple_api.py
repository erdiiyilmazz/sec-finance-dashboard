from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# Import functions from our get_companies.py script
from get_companies import get_ticker_cik_mappings, get_company_info, get_all_companies, get_company_10k_filings, get_company_facts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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

@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Simple SEC API is running"}

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
        mappings = get_ticker_cik_mappings()
        if not mappings:
            raise HTTPException(status_code=500, detail="Failed to synchronize CIK-ticker mappings")
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

if __name__ == "__main__":
    uvicorn.run("simple_api:app", host="0.0.0.0", port=8001, reload=False) 