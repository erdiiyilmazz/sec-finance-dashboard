import yfinance as yf
import numpy as np
import logging
import os
import json
import requests
import random
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockService:
    """Service for fetching stock price data."""
    
    def __init__(self, cache_dir="cache/stocks"):
        """Initialize the stock service with caching."""
        self.cache_dir = cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Alpha Vantage API key - replace with your own if you have one
        # Get a free API key from: https://www.alphavantage.co/support/#api-key
        self.alpha_vantage_api_key = "demo"  # Use "demo" for testing, but it's very limited
    
    def get_stock_data(self, ticker, period="1y", force_refresh=False):
        """
        Get stock price data for a specific ticker.
        
        Args:
            ticker (str): The stock ticker symbol
            period (str): Time period to fetch (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            force_refresh (bool): Whether to force a refresh from the API
            
        Returns:
            dict: Stock data including prices and performance metrics
        """
        ticker = ticker.upper()
        cache_file = os.path.join(self.cache_dir, f"{ticker}_{period}.json")
        
        # Check cache first if not forcing refresh
        if not force_refresh and os.path.exists(cache_file):
            # Check if cache is recent (less than 24 hours old)
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_age < timedelta(hours=24):
                logger.info(f"Using cached data for {ticker} ({period})")
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.warning(f"Error reading cache for {ticker}: {e}")
        
        try:
            # First try Alpha Vantage API
            logger.info(f"Fetching stock data for {ticker} from Alpha Vantage API")
            stock_data = self._fetch_from_alpha_vantage(ticker)
            
            if not stock_data:
                # If Alpha Vantage fails, try Yahoo Finance as backup
                logger.info(f"Alpha Vantage failed, trying Yahoo Finance for {ticker}")
                stock_data = self._fetch_from_yahoo(ticker, period)
            
            if not stock_data:
                # If both APIs fail, use fallback data
                logger.warning(f"All APIs failed for {ticker}, using fallback data")
                return self._generate_fallback_data(ticker, period)
            
            # Calculate additional metrics
            result = self._calculate_metrics(ticker, stock_data)
            
            # Cache the results
            with open(cache_file, 'w') as f:
                json.dump(result, f, default=self._json_serial)
            
            return result
        
        except Exception as e:
            logger.error(f"Error fetching stock data for {ticker}: {e}")
            logger.info(f"Using fallback data for {ticker}")
            return self._generate_fallback_data(ticker, period)
    
    def _fetch_from_alpha_vantage(self, ticker):
        """Fetch stock data from Alpha Vantage API."""
        try:
            # Alpha Vantage API endpoint for daily time series
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&outputsize=compact&apikey={self.alpha_vantage_api_key}"
            
            response = requests.get(url)
            data = response.json()
            
            # Check if we got valid data
            if "Time Series (Daily)" not in data:
                logger.warning(f"Alpha Vantage API did not return valid data for {ticker}: {data}")
                return None
            
            # Parse the data
            time_series = data["Time Series (Daily)"]
            stock_data = []
            
            for date, values in time_series.items():
                stock_data.append({
                    "date": date,
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"])
                })
            
            # Sort by date (oldest first)
            stock_data.sort(key=lambda x: x["date"])
            
            return stock_data
        
        except Exception as e:
            logger.error(f"Error fetching from Alpha Vantage: {e}")
            return None
    
    def _fetch_from_yahoo(self, ticker, period):
        """Fetch stock data from Yahoo Finance as a backup."""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            
            # Check if we got valid data
            if hist.empty:
                logger.warning(f"Yahoo Finance did not return valid data for {ticker}")
                return None
            
            # Convert DataFrame to list
            stock_data = []
            for date, row in hist.iterrows():
                stock_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"])
                })
            
            return stock_data
        
        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance: {e}")
            return None
    
    def _generate_fallback_data(self, ticker, period):
        """Generate fallback sample data when API fails."""
        logger.info(f"Generating fallback data for {ticker}")
        
        # Determine number of days based on period
        days = 252  # Default to 1 year (approx trading days)
        if period == "1mo":
            days = 21
        elif period == "3mo":
            days = 63
        elif period == "6mo":
            days = 126
        elif period == "2y":
            days = 504
        elif period == "5y":
            days = 1260
        
        # Generate dates
        end_date = datetime.now()
        dates = [(end_date - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
        dates.reverse()  # Oldest to newest
        
        # Generate price data with realistic movement
        base_price = 150.0  # Starting price
        if ticker == "AAPL":
            base_price = 150.0
        elif ticker == "MSFT":
            base_price = 300.0
        elif ticker == "GOOGL":
            base_price = 120.0
        elif ticker == "AMZN":
            base_price = 130.0
        elif ticker == "NVDA":
            base_price = 400.0
        
        # Generate stock data with some randomness but trending upward
        stock_data = []
        current_price = base_price
        for date in dates:
            # Random daily change between -2% and +2% with slight upward bias
            daily_change = random.uniform(-0.02, 0.025)
            current_price *= (1 + daily_change)
            
            # Add some volatility
            high = current_price * (1 + random.uniform(0, 0.01))
            low = current_price * (1 - random.uniform(0, 0.01))
            open_price = current_price * (1 + random.uniform(-0.005, 0.005))
            
            stock_data.append({
                "date": date,
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(current_price, 2),
                "volume": int(random.uniform(20000000, 100000000))
            })
        
        # Calculate changes
        result = self._calculate_metrics(ticker, stock_data)
        result["is_fallback_data"] = True  # Flag to indicate this is fallback data
        
        return result
    
    def _calculate_metrics(self, ticker, stock_data):
        """Calculate performance metrics from historical data."""
        # Calculate percentage changes
        changes = {}
        if len(stock_data) > 0:
            latest_price = stock_data[-1]["close"]
            
            # Daily change
            if len(stock_data) > 1:
                prev_day_price = stock_data[-2]["close"]
                changes["daily"] = (latest_price - prev_day_price) / prev_day_price
            
            # Weekly change (5 trading days)
            if len(stock_data) > 5:
                week_ago_price = stock_data[-6]["close"]
                changes["weekly"] = (latest_price - week_ago_price) / week_ago_price
            
            # Monthly change (21 trading days)
            if len(stock_data) > 21:
                month_ago_price = stock_data[-22]["close"]
                changes["monthly"] = (latest_price - month_ago_price) / month_ago_price
            
            # 3-month change (63 trading days)
            if len(stock_data) > 63:
                three_month_ago_price = stock_data[-64]["close"]
                changes["three_month"] = (latest_price - three_month_ago_price) / three_month_ago_price
            
            # 6-month change (126 trading days)
            if len(stock_data) > 126:
                six_month_ago_price = stock_data[-127]["close"]
                changes["six_month"] = (latest_price - six_month_ago_price) / six_month_ago_price
            
            # Year-to-date change
            first_day_of_year = datetime(datetime.now().year, 1, 1).strftime("%Y-%m-%d")
            ytd_data = [d for d in stock_data if d["date"] >= first_day_of_year]
            if len(ytd_data) > 0:
                ytd_start_price = ytd_data[0]["close"]
                changes["ytd"] = (latest_price - ytd_start_price) / ytd_start_price
            
            # 1-year change
            if len(stock_data) > 252:  # Approximately 252 trading days in a year
                year_ago_price = stock_data[-253]["close"]
                changes["yearly"] = (latest_price - year_ago_price) / year_ago_price
        
        # Get basic info
        info = {}
        try:
            # Try to get company info from Yahoo Finance
            stock = yf.Ticker(ticker)
            info_data = stock.info
            
            # Extract relevant info
            info = {
                "name": info_data.get("shortName", ""),
                "sector": info_data.get("sector", ""),
                "industry": info_data.get("industry", ""),
                "market_cap": info_data.get("marketCap", None),
                "pe_ratio": info_data.get("trailingPE", None),
                "dividend_yield": info_data.get("dividendYield", None),
                "fifty_two_week_high": info_data.get("fiftyTwoWeekHigh", None),
                "fifty_two_week_low": info_data.get("fiftyTwoWeekLow", None)
            }
        except Exception as e:
            logger.warning(f"Error fetching info for {ticker}: {e}")
            # Use basic info if Yahoo Finance fails
            company_names = {
                "AAPL": "Apple Inc.",
                "MSFT": "Microsoft Corporation",
                "GOOGL": "Alphabet Inc.",
                "AMZN": "Amazon.com, Inc.",
                "NVDA": "NVIDIA Corporation"
            }
            info = {
                "name": company_names.get(ticker, f"{ticker} Inc."),
                "sector": "Technology",
                "industry": "General",
            }
        
        return {
            "ticker": ticker,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "latest_price": stock_data[-1]["close"] if stock_data else None,
            "stock_data": stock_data,
            "changes": changes,
            "info": info
        }
    
    def _json_serial(self, obj):
        """JSON serializer for objects not serializable by default json code."""
        if isinstance(obj, (datetime, np.datetime64)):
            return obj.strftime("%Y-%m-%d")
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        raise TypeError(f"Type {type(obj)} not serializable") 