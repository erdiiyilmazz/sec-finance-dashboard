import json
import sys
from services.sec_api_service import SECAPIService

# Initialize the SEC API service
sec_service = SECAPIService(
    user_agent="SEC Dashboard (youremail@email.com, +90-XXX-XXX-XXXX)"
)

def get_ticker_cik_mappings():
    """Fetch ticker-CIK mappings from SEC's ticker.txt file."""
    try:
        # Use the service to get company tickers
        mappings = sec_service.get_company_tickers(force_refresh=False)
        return mappings
    except Exception as e:
        print(f"Error fetching ticker-CIK mappings: {e}")
        return {}

def get_company_info(ticker):
    """Get company information for a specific ticker."""
    mappings = get_ticker_cik_mappings()
    
    if not ticker.upper() in mappings:
        return {"error": f"Ticker {ticker} not found in SEC database"}
    
    cik = mappings[ticker.upper()]
    
    try:
        # Use the service to get company submissions
        submissions = sec_service.get_company_submissions(cik)
        
        # Extract relevant information
        company_info = {
            "ticker": ticker.upper(),
            "cik": cik,
            "name": submissions.get("name", ""),
            "sic": submissions.get("sic", ""),
            "sicDescription": submissions.get("sicDescription", ""),
            "website": submissions.get("website", ""),
            "fiscalYearEnd": submissions.get("fiscalYearEnd", ""),
            "stateOfIncorporation": submissions.get("stateOfIncorporation", "")
        }
        
        return company_info
    except Exception as e:
        return {"error": f"Error fetching company info: {e}"}

def get_company_10k_filings(ticker, limit=5):
    """Get 10-K filings for a specific company."""
    mappings = get_ticker_cik_mappings()
    
    if not ticker.upper() in mappings:
        return {"error": f"Ticker {ticker} not found in SEC database"}
    
    cik = mappings[ticker.upper()]
    
    try:
        # Use the service to get company submissions
        submissions = sec_service.get_company_submissions(cik)
        
        # Extract filing information
        filings = []
        recent_filings = submissions.get("filings", {}).get("recent", {})
        
        if not recent_filings:
            return {"error": "No filings found for this company"}
        
        # Get the indices of 10-K filings
        form_types = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        accession_numbers = recent_filings.get("accessionNumber", [])
        primary_documents = recent_filings.get("primaryDocument", [])
        file_numbers = recent_filings.get("fileNumber", [])
        
        # Find 10-K filings
        ten_k_indices = [i for i, form in enumerate(form_types) if form == "10-K"]
        
        # Extract 10-K filing information
        for idx in ten_k_indices[:limit]:  # Limit to the most recent 'limit' filings
            if idx < len(filing_dates) and idx < len(accession_numbers):
                # Format the accession number for the URL
                acc_no = accession_numbers[idx].replace('-', '')
                
                # Create the Edgar URL for the filing
                edgar_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no}/{primary_documents[idx]}"
                
                filing = {
                    "form": "10-K",
                    "filingDate": filing_dates[idx],
                    "accessionNumber": accession_numbers[idx],
                    "primaryDocument": primary_documents[idx] if idx < len(primary_documents) else "",
                    "fileNumber": file_numbers[idx] if idx < len(file_numbers) else "",
                    "edgarUrl": edgar_url
                }
                filings.append(filing)
        
        return {
            "ticker": ticker.upper(),
            "cik": cik,
            "name": submissions.get("name", ""),
            "filings": filings
        }
    except Exception as e:
        return {"error": f"Error fetching 10-K filings: {e}"}

def get_all_companies(limit=20):
    """Get a list of companies (limited to avoid overwhelming the API)."""
    mappings = get_ticker_cik_mappings()
    companies = []
    
    # If limit is 0, return all companies
    if limit == 0:
        for ticker, cik in mappings.items():
            companies.append({
                "ticker": ticker,
                "cik": cik
            })
        return companies
    
    # Otherwise, get the first 'limit' companies
    count = 0
    for ticker, cik in list(mappings.items())[:limit]:
        companies.append({
            "ticker": ticker,
            "cik": cik
        })
        count += 1
        if count >= limit:
            break
    
    return companies

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If ticker is provided as argument, get specific company info
        ticker = sys.argv[1]
        result = get_company_info(ticker)
    else:
        # Otherwise, get list of companies
        result = get_all_companies()
    
    print(json.dumps(result, indent=2)) 