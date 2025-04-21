from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
import logging
import numpy as np
from collections import defaultdict

from models.company import Company
from models.financial_metric import FinancialMetric, MetricPeriod
from repositories.company_repository import CompanyRepository
from repositories.financial_metric_repository import FinancialMetricRepository


class FinancialAnalysisService:
    """
    Service for analyzing financial metrics and generating insights.
    """
    
    def __init__(self, 
                 company_repository: CompanyRepository,
                 metric_repository: FinancialMetricRepository):
        """
        Initialize the financial analysis service.
        
        Args:
            company_repository: Repository for managing companies
            metric_repository: Repository for managing financial metrics
        """
        self.company_repo = company_repository
        self.metric_repo = metric_repository
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def get_metric_time_series(self, ticker: str, metric_name: str, 
                              period: MetricPeriod = MetricPeriod.ANNUAL) -> List[Tuple[datetime, float]]:
        """
        Get a time series of values for a specific metric.
        
        Args:
            ticker: Ticker symbol of the company
            metric_name: Name of the metric
            period: Period type (annual, quarterly, etc.)
            
        Returns:
            List of (date, value) pairs
        """
        company = self.company_repo.get_by_ticker(ticker)
        if not company:
            self.logger.error(f"Company with ticker {ticker} not found")
            return []
        
        return self.metric_repo.get_time_series(company.ticker, metric_name, period)
    
    def calculate_growth_rates(self, ticker: str, metric_name: str, 
                              period: MetricPeriod = MetricPeriod.ANNUAL) -> List[Tuple[datetime, float]]:
        """
        Calculate year-over-year growth rates for a specific metric.
        
        Args:
            ticker: Ticker symbol of the company
            metric_name: Name of the metric
            period: Period type (annual, quarterly, etc.)
            
        Returns:
            List of (date, growth_rate) pairs
        """
        # Get time series data
        time_series = self.get_metric_time_series(ticker, metric_name, period)
        
        if len(time_series) < 2:
            return []
        
        # Sort by date
        time_series.sort(key=lambda x: x[0])
        
        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(time_series)):
            current_date, current_value = time_series[i]
            _, previous_value = time_series[i-1]
            
            if previous_value == 0:
                growth_rate = float('inf') if current_value > 0 else float('-inf')
            else:
                growth_rate = (current_value - previous_value) / abs(previous_value)
            
            growth_rates.append((current_date, growth_rate))
        
        return growth_rates
    
    def calculate_cagr(self, ticker: str, metric_name: str, 
                      years: int = 5) -> Optional[float]:
        """
        Calculate Compound Annual Growth Rate (CAGR) for a specific metric.
        
        Args:
            ticker: Ticker symbol of the company
            metric_name: Name of the metric
            years: Number of years to calculate CAGR for
            
        Returns:
            CAGR as a decimal (e.g., 0.1 for 10%)
        """
        # Get time series data
        time_series = self.get_metric_time_series(ticker, metric_name, MetricPeriod.ANNUAL)
        
        if len(time_series) < 2:
            return None
        
        # Sort by date
        time_series.sort(key=lambda x: x[0])
        
        # Get the most recent value and the value 'years' ago
        if len(time_series) <= years:
            start_value = time_series[0][1]
            end_value = time_series[-1][1]
            actual_years = len(time_series) - 1
        else:
            start_value = time_series[-years-1][1]
            end_value = time_series[-1][1]
            actual_years = years
        
        # Calculate CAGR
        if start_value <= 0 or end_value <= 0:
            return None
        
        cagr = (end_value / start_value) ** (1 / actual_years) - 1
        return cagr
    
    def calculate_financial_ratios(self, ticker: str) -> Dict[str, float]:
        """
        Calculate common financial ratios for a company.
        
        Args:
            ticker: Ticker symbol of the company
            
        Returns:
            Dictionary of financial ratios
        """
        company = self.company_repo.get_by_ticker(ticker)
        if not company:
            self.logger.error(f"Company with ticker {ticker} not found")
            return {}
        
        # Get the most recent annual metrics
        metrics = self.metric_repo.find_by_company_and_metric(company.ticker, None, MetricPeriod.ANNUAL)
        
        # Group metrics by name and get the most recent for each
        latest_metrics = {}
        for metric in metrics:
            if metric.name not in latest_metrics or metric.date > latest_metrics[metric.name].date:
                latest_metrics[metric.name] = metric
        
        # Calculate ratios
        ratios = {}
        
        # Return on Assets (ROA)
        if "NetIncome" in latest_metrics and "TotalAssets" in latest_metrics:
            net_income = latest_metrics["NetIncome"].value
            total_assets = latest_metrics["TotalAssets"].value
            if total_assets != 0:
                ratios["ROA"] = net_income / total_assets
        
        # Return on Equity (ROE)
        if "NetIncome" in latest_metrics and "StockholdersEquity" in latest_metrics:
            net_income = latest_metrics["NetIncome"].value
            equity = latest_metrics["StockholdersEquity"].value
            if equity != 0:
                ratios["ROE"] = net_income / equity
        
        # Debt to Equity
        if "TotalLiabilities" in latest_metrics and "StockholdersEquity" in latest_metrics:
            liabilities = latest_metrics["TotalLiabilities"].value
            equity = latest_metrics["StockholdersEquity"].value
            if equity != 0:
                ratios["DebtToEquity"] = liabilities / equity
        
        # Profit Margin
        if "NetIncome" in latest_metrics and "Revenue" in latest_metrics:
            net_income = latest_metrics["NetIncome"].value
            revenue = latest_metrics["Revenue"].value
            if revenue != 0:
                ratios["ProfitMargin"] = net_income / revenue
        
        return ratios
    
    def compare_companies(self, tickers: List[str], metric_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Compare multiple companies based on a specific metric.
        
        Args:
            tickers: List of ticker symbols
            metric_name: Name of the metric to compare
            
        Returns:
            Dictionary mapping tickers to metric data
        """
        results = {}
        
        for ticker in tickers:
            company = self.company_repo.get_by_ticker(ticker)
            if not company:
                self.logger.warning(f"Company with ticker {ticker} not found")
                continue
            
            # Get time series data
            time_series = self.get_metric_time_series(ticker, metric_name, MetricPeriod.ANNUAL)
            
            if not time_series:
                self.logger.warning(f"No {metric_name} data found for {ticker}")
                continue
            
            # Sort by date
            time_series.sort(key=lambda x: x[0])
            
            # Calculate growth rate
            growth_rate = None
            if len(time_series) >= 2:
                latest_value = time_series[-1][1]
                previous_value = time_series[-2][1]
                if previous_value != 0:
                    growth_rate = (latest_value - previous_value) / abs(previous_value)
            
            # Calculate CAGR
            cagr = self.calculate_cagr(ticker, metric_name)
            
            # Store results
            results[ticker] = {
                "company_name": company.name,
                "latest_value": time_series[-1][1] if time_series else None,
                "latest_date": time_series[-1][0] if time_series else None,
                "growth_rate": growth_rate,
                "cagr": cagr,
                "time_series": time_series
            }
        
        return results
    
    def get_sector_averages(self, sector: str, metric_name: str) -> Dict[str, float]:
        """
        Calculate sector averages for a specific metric.
        
        Args:
            sector: Sector name
            metric_name: Name of the metric
            
        Returns:
            Dictionary of sector averages
        """
        # Get companies in the sector
        companies = self.company_repo.find_by_sector(sector)
        
        if not companies:
            self.logger.warning(f"No companies found in sector {sector}")
            return {}
        
        # Collect latest metric values
        values = []
        for company in companies:
            metrics = self.metric_repo.find_by_company_and_metric(
                company.ticker, metric_name, MetricPeriod.ANNUAL)
            
            if not metrics:
                continue
            
            # Get the most recent metric
            latest_metric = max(metrics, key=lambda m: m.date)
            values.append(latest_metric.value)
        
        if not values:
            return {}
        
        # Calculate statistics
        return {
            "mean": np.mean(values),
            "median": np.median(values),
            "min": np.min(values),
            "max": np.max(values),
            "std": np.std(values),
            "count": len(values)
        }

# Helper functions for working with financial data
def get_latest_value(facts: Dict[str, Any], metric_name: str, 
                    taxonomy: str = "us-gaap") -> Optional[float]:
    """
    Extract the latest value for a specific metric from company facts.
    
    Args:
        facts: The company facts dictionary from SEC API
        metric_name: The name of the metric to extract
        taxonomy: The taxonomy to use (default: us-gaap)
        
    Returns:
        The latest value as a float, or None if not found
    """
    try:
        # Navigate to the right section of the facts dictionary
        if not facts or 'facts' not in facts:
            return None
            
        taxonomy_data = facts.get('facts', {}).get(taxonomy, {})
        metric_data = taxonomy_data.get(metric_name, {})
        
        if not metric_data or 'units' not in metric_data:
            return None
            
        # Most financial values are in USD
        units = metric_data.get('units', {}).get('USD', [])
        if not units:
            # Try other unit types if USD not found
            for unit_type, values in metric_data.get('units', {}).items():
                if values:
                    units = values
                    break
        
        if not units:
            return None
            
        # Find the latest value by date
        latest_item = max(units, key=lambda x: x.get('end', '0000-00-00'))
        return float(latest_item.get('val', 0))
        
    except Exception as e:
        logger.error(f"Error extracting {metric_name}: {str(e)}")
        return None

def get_latest_year(facts: Dict[str, Any], metric_name: str, 
                   taxonomy: str = "us-gaap") -> Optional[int]:
    """
    Extract the latest year for a specific metric from company facts.
    
    Args:
        facts: The company facts dictionary from SEC API
        metric_name: The name of the metric to extract
        taxonomy: The taxonomy to use (default: us-gaap)
        
    Returns:
        The latest year as an integer, or None if not found
    """
    try:
        # Navigate to the right section of the facts dictionary
        if not facts or 'facts' not in facts:
            return None
            
        taxonomy_data = facts.get('facts', {}).get(taxonomy, {})
        metric_data = taxonomy_data.get(metric_name, {})
        
        if not metric_data or 'units' not in metric_data:
            return None
            
        # Most financial values are in USD
        units = metric_data.get('units', {}).get('USD', [])
        if not units:
            # Try other unit types if USD not found
            for unit_type, values in metric_data.get('units', {}).items():
                if values:
                    units = values
                    break
        
        if not units:
            return None
            
        # Find the latest value by date
        latest_item = max(units, key=lambda x: x.get('end', '0000-00-00'))
        end_date = latest_item.get('end', '')
        
        # Extract year from date
        if end_date and len(end_date) >= 4:
            return int(end_date[:4])
        return None
        
    except Exception as e:
        logger.error(f"Error extracting year for {metric_name}: {str(e)}")
        return None

# Financial ratio calculation functions
def calculate_current_ratio(facts: Dict[str, Any]) -> Optional[float]:
    """
    Calculate current ratio: Current Assets / Current Liabilities
    
    Args:
        facts: The company facts dictionary from SEC API
        
    Returns:
        Current ratio as a float, or None if data not available
    """
    current_assets = get_latest_value(facts, "AssetsCurrent")
    current_liabilities = get_latest_value(facts, "LiabilitiesCurrent")
    
    if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
        return round(current_assets / current_liabilities, 2)
    return None

def calculate_quick_ratio(facts: Dict[str, Any]) -> Optional[float]:
    """
    Calculate quick ratio: (Current Assets - Inventory) / Current Liabilities
    
    Args:
        facts: The company facts dictionary from SEC API
        
    Returns:
        Quick ratio as a float, or None if data not available
    """
    current_assets = get_latest_value(facts, "AssetsCurrent")
    inventory = get_latest_value(facts, "InventoryNet")
    current_liabilities = get_latest_value(facts, "LiabilitiesCurrent")
    
    if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
        # Use 0 as default if inventory is None
        inventory = inventory or 0
        return round((current_assets - inventory) / current_liabilities, 2)
    return None

def calculate_debt_to_equity_ratio(facts: Dict[str, Any]) -> Optional[float]:
    """
    Calculate debt to equity ratio: Total Liabilities / Stockholders Equity
    
    Args:
        facts: The company facts dictionary from SEC API
        
    Returns:
        Debt to equity ratio as a float, or None if data not available
    """
    total_liabilities = get_latest_value(facts, "Liabilities")
    
    # Try different possible names for stockholders equity
    equity_options = [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "StockholdersEquityAttributableToParent"
    ]
    
    stockholders_equity = None
    for option in equity_options:
        stockholders_equity = get_latest_value(facts, option)
        if stockholders_equity is not None:
            break
    
    if total_liabilities is not None and stockholders_equity is not None and stockholders_equity > 0:
        return round(total_liabilities / stockholders_equity, 2)
    return None

def calculate_return_on_assets(facts: Dict[str, Any]) -> Optional[float]:
    """
    Calculate return on assets: Net Income / Total Assets
    
    Args:
        facts: The company facts dictionary from SEC API
        
    Returns:
        ROA as a float, or None if data not available
    """
    net_income = get_latest_value(facts, "NetIncomeLoss")
    total_assets = get_latest_value(facts, "Assets")
    
    if net_income is not None and total_assets is not None and total_assets > 0:
        return round((net_income / total_assets) * 100, 2)  # Return as percentage
    return None

def calculate_return_on_equity(facts: Dict[str, Any]) -> Optional[float]:
    """
    Calculate return on equity: Net Income / Stockholders Equity
    
    Args:
        facts: The company facts dictionary from SEC API
        
    Returns:
        ROE as a float, or None if data not available
    """
    net_income = get_latest_value(facts, "NetIncomeLoss")
    
    # Try different possible names for stockholders equity
    equity_options = [
        "StockholdersEquity",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        "StockholdersEquityAttributableToParent"
    ]
    
    stockholders_equity = None
    for option in equity_options:
        stockholders_equity = get_latest_value(facts, option)
        if stockholders_equity is not None:
            break
    
    if net_income is not None and stockholders_equity is not None and stockholders_equity > 0:
        return round((net_income / stockholders_equity) * 100, 2)  # Return as percentage
    return None

def calculate_gross_margin(facts: Dict[str, Any]) -> Optional[float]:
    """
    Calculate gross margin: (Revenue - Cost of Goods Sold) / Revenue
    
    Args:
        facts: The company facts dictionary from SEC API
        
    Returns:
        Gross margin as a percentage, or None if data not available
    """
    revenue = get_latest_value(facts, "Revenue")
    cogs = get_latest_value(facts, "CostOfGoodsSold")
    
    if revenue is not None and cogs is not None and revenue > 0:
        return round(((revenue - cogs) / revenue) * 100, 2)  # Return as percentage
    return None

def calculate_net_profit_margin(facts: Dict[str, Any]) -> Optional[float]:
    """
    Calculate net profit margin: Net Income / Revenue
    
    Args:
        facts: The company facts dictionary from SEC API
        
    Returns:
        Net profit margin as a percentage, or None if data not available
    """
    net_income = get_latest_value(facts, "NetIncomeLoss")
    revenue = get_latest_value(facts, "Revenue")
    
    if net_income is not None and revenue is not None and revenue > 0:
        return round((net_income / revenue) * 100, 2)  # Return as percentage
    return None

def calculate_price_to_earnings_ratio(facts: Dict[str, Any], current_price: float) -> Optional[float]:
    """
    Calculate P/E ratio: Current Stock Price / Earnings Per Share
    
    Args:
        facts: The company facts dictionary from SEC API
        current_price: Current stock price
        
    Returns:
        P/E ratio as a float, or None if data not available
    """
    eps = get_latest_value(facts, "EarningsPerShareBasic")
    
    if eps is not None and eps > 0 and current_price is not None:
        return round(current_price / eps, 2)
    return None

def calculate_all_ratios(facts: Dict[str, Any], current_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate all financial ratios for a company.
    
    Args:
        facts: The company facts dictionary from SEC API
        current_price: Current stock price (optional)
        
    Returns:
        Dictionary containing all calculated ratios with their values and years
    """
    ratios = {
        "liquidity_ratios": {
            "current_ratio": {
                "value": calculate_current_ratio(facts),
                "description": "Measures a company's ability to pay short-term obligations",
                "formula": "Current Assets / Current Liabilities",
                "interpretation": {
                    "good": "> 1.5",
                    "concern": "< 1.0"
                },
                "year": get_latest_year(facts, "AssetsCurrent")
            },
            "quick_ratio": {
                "value": calculate_quick_ratio(facts),
                "description": "Measures a company's ability to pay short-term obligations with its most liquid assets",
                "formula": "(Current Assets - Inventory) / Current Liabilities",
                "interpretation": {
                    "good": "> 1.0",
                    "concern": "< 0.7"
                },
                "year": get_latest_year(facts, "AssetsCurrent")
            }
        },
        "solvency_ratios": {
            "debt_to_equity": {
                "value": calculate_debt_to_equity_ratio(facts),
                "description": "Measures a company's financial leverage",
                "formula": "Total Liabilities / Stockholders' Equity",
                "interpretation": {
                    "good": "< 1.5",
                    "concern": "> 2.0"
                },
                "year": get_latest_year(facts, "Liabilities")
            }
        },
        "profitability_ratios": {
            "return_on_assets": {
                "value": calculate_return_on_assets(facts),
                "description": "Measures how efficiently a company is using its assets to generate profit",
                "formula": "(Net Income / Total Assets) * 100%",
                "interpretation": {
                    "good": "> 5%",
                    "concern": "< 2%"
                },
                "year": get_latest_year(facts, "Assets")
            },
            "return_on_equity": {
                "value": calculate_return_on_equity(facts),
                "description": "Measures how efficiently a company is using its equity to generate profit",
                "formula": "(Net Income / Stockholders' Equity) * 100%",
                "interpretation": {
                    "good": "> 15%",
                    "concern": "< 10%"
                },
                "year": get_latest_year(facts, "StockholdersEquity")
            },
            "gross_margin": {
                "value": calculate_gross_margin(facts),
                "description": "Measures the percentage of revenue that exceeds the cost of goods sold",
                "formula": "((Revenue - COGS) / Revenue) * 100%",
                "interpretation": {
                    "good": "Industry dependent, higher is better",
                    "concern": "Declining over time"
                },
                "year": get_latest_year(facts, "Revenue")
            },
            "net_profit_margin": {
                "value": calculate_net_profit_margin(facts),
                "description": "Measures how much net profit is generated as a percentage of revenue",
                "formula": "(Net Income / Revenue) * 100%",
                "interpretation": {
                    "good": "> 10%",
                    "concern": "< 5%"
                },
                "year": get_latest_year(facts, "Revenue")
            }
        }
    }
    
    # Add P/E ratio if current price is provided
    if current_price is not None:
        ratios["valuation_ratios"] = {
            "price_to_earnings": {
                "value": calculate_price_to_earnings_ratio(facts, current_price),
                "description": "Measures the current share price relative to earnings per share",
                "formula": "Current Stock Price / Earnings Per Share",
                "interpretation": {
                    "good": "Industry dependent, 10-20 is typical",
                    "concern": "> 30 may indicate overvaluation"
                },
                "year": get_latest_year(facts, "EarningsPerShareBasic")
            }
        }
    
    # Add metadata
    ratios["metadata"] = {
        "calculated_at": datetime.now().isoformat(),
        "data_year": get_latest_year(facts, "Revenue") or get_latest_year(facts, "Assets")
    }
    
    return ratios 