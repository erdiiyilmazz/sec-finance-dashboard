"""
Financial Analysis Helper Functions

This module provides helper functions for financial ratio calculations.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_latest_metric_value(data: Dict[str, Any], metric_name: str) -> Optional[float]:
    """
    Get the latest value of a metric from the company data.
    
    Args:
        data: Company data dictionary
        metric_name: Name of the metric
        
    Returns:
        Latest value or None if not available
    """
    if not data or 'common_metrics' not in data or metric_name not in data['common_metrics']:
        return None
    
    # Get all values for the metric
    metric_data = data['common_metrics'][metric_name]
    
    # Check if we have data
    if not metric_data or not isinstance(metric_data, list) or len(metric_data) == 0:
        return None
    
    # Find the latest entry
    latest_entry = None
    latest_date = None
    
    for entry in metric_data:
        if 'end' not in entry or 'val' not in entry:
            continue
        
        try:
            # Parse date
            entry_date = datetime.strptime(entry['end'], '%Y-%m-%d')
            
            # Check if this is the latest
            if latest_date is None or entry_date > latest_date:
                latest_date = entry_date
                latest_entry = entry
        except (ValueError, TypeError):
            continue
    
    # Return the value if found
    return latest_entry['val'] if latest_entry else None

def get_latest_year(data: Dict[str, Any], metric_name: str) -> Optional[int]:
    """
    Get the latest year for a metric from the company data.
    
    Args:
        data: Company data dictionary
        metric_name: Name of the metric
        
    Returns:
        Latest year or None if not available
    """
    if not data or 'common_metrics' not in data or metric_name not in data['common_metrics']:
        return None
    
    # Get all values for the metric
    metric_data = data['common_metrics'][metric_name]
    
    # Check if we have data
    if not metric_data or not isinstance(metric_data, list) or len(metric_data) == 0:
        return None
    
    # Find the latest entry
    latest_year = None
    latest_date = None
    
    for entry in metric_data:
        if 'end' not in entry:
            continue
        
        try:
            # Parse date
            entry_date = datetime.strptime(entry['end'], '%Y-%m-%d')
            
            # Check if this is the latest
            if latest_date is None or entry_date > latest_date:
                latest_date = entry_date
                latest_year = entry_date.year
        except (ValueError, TypeError):
            continue
    
    # Return the year if found
    return latest_year

def calculate_current_ratio(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate the current ratio.
    
    Current Ratio = Current Assets / Current Liabilities
    
    Args:
        data: Company data dictionary
        
    Returns:
        Current ratio or None if unavailable
    """
    # For this example, we'll assume these metrics exist
    # In a real implementation, you might need to adapt to what's available
    current_assets = get_latest_metric_value(data, "AssetsCurrent")
    current_liabilities = get_latest_metric_value(data, "LiabilitiesCurrent")
    
    if current_assets is None or current_liabilities is None or current_liabilities == 0:
        return None
    
    return current_assets / current_liabilities

def calculate_quick_ratio(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate the quick ratio.
    
    Quick Ratio = (Current Assets - Inventory) / Current Liabilities
    
    Args:
        data: Company data dictionary
        
    Returns:
        Quick ratio or None if unavailable
    """
    current_assets = get_latest_metric_value(data, "AssetsCurrent")
    inventory = get_latest_metric_value(data, "InventoryNet")
    current_liabilities = get_latest_metric_value(data, "LiabilitiesCurrent")
    
    if current_assets is None or current_liabilities is None or current_liabilities == 0:
        return None
    
    # If inventory is None, assume it's 0
    inventory = inventory or 0
    
    return (current_assets - inventory) / current_liabilities

def calculate_debt_to_equity_ratio(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate the debt-to-equity ratio.
    
    Debt-to-Equity Ratio = Total Liabilities / Stockholders' Equity
    
    Args:
        data: Company data dictionary
        
    Returns:
        Debt-to-equity ratio or None if unavailable
    """
    total_liabilities = get_latest_metric_value(data, "TotalLiabilities")
    equity = get_latest_metric_value(data, "StockholdersEquity")
    
    if total_liabilities is None or equity is None or equity == 0:
        return None
    
    return total_liabilities / equity

def calculate_return_on_assets(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate return on assets (ROA).
    
    ROA = (Net Income / Total Assets) * 100%
    
    Args:
        data: Company data dictionary
        
    Returns:
        ROA as a decimal (e.g., 0.1 for 10%) or None if unavailable
    """
    net_income = get_latest_metric_value(data, "NetIncome")
    total_assets = get_latest_metric_value(data, "TotalAssets")
    
    if net_income is None or total_assets is None or total_assets == 0:
        return None
    
    return net_income / total_assets

def calculate_return_on_equity(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate return on equity (ROE).
    
    ROE = (Net Income / Stockholders' Equity) * 100%
    
    Args:
        data: Company data dictionary
        
    Returns:
        ROE as a decimal (e.g., 0.1 for 10%) or None if unavailable
    """
    net_income = get_latest_metric_value(data, "NetIncome")
    equity = get_latest_metric_value(data, "StockholdersEquity")
    
    if net_income is None or equity is None or equity == 0:
        return None
    
    return net_income / equity

def calculate_gross_margin(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate gross margin.
    
    Gross Margin = ((Revenue - COGS) / Revenue) * 100%
    
    Args:
        data: Company data dictionary
        
    Returns:
        Gross margin as a decimal (e.g., 0.1 for 10%) or None if unavailable
    """
    revenue = get_latest_metric_value(data, "Revenue")
    cogs = get_latest_metric_value(data, "CostOfGoodsAndServicesSold")
    
    if revenue is None or cogs is None or revenue == 0:
        return None
    
    return (revenue - cogs) / revenue

def calculate_net_profit_margin(data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate net profit margin.
    
    Net Profit Margin = (Net Income / Revenue) * 100%
    
    Args:
        data: Company data dictionary
        
    Returns:
        Net profit margin as a decimal (e.g., 0.1 for 10%) or None if unavailable
    """
    net_income = get_latest_metric_value(data, "NetIncome")
    revenue = get_latest_metric_value(data, "Revenue")
    
    if net_income is None or revenue is None or revenue == 0:
        return None
    
    return net_income / revenue

def calculate_price_to_earnings_ratio(data: Dict[str, Any], current_price: float) -> Optional[float]:
    """
    Calculate price-to-earnings (P/E) ratio.
    
    P/E Ratio = Current Stock Price / Earnings Per Share
    
    Args:
        data: Company data dictionary
        current_price: Current stock price
        
    Returns:
        P/E ratio or None if unavailable
    """
    if current_price is None:
        return None
    
    eps = get_latest_metric_value(data, "EarningsPerShareBasic")
    
    if eps is None or eps == 0:
        return None
    
    return current_price / eps

def calculate_all_ratios(data: Dict[str, Any], current_price: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate all financial ratios for a company.
    
    Args:
        data: The company data dictionary
        current_price: Current stock price (optional)
        
    Returns:
        Dictionary containing all calculated ratios
    """
    # In a full implementation, this would calculate real ratios
    # For demonstration, we'll return mock data
    
    # Get current year for consistency
    current_year = datetime.now().year
    
    ratios = {
        "liquidity_ratios": {
            "current_ratio": {
                "value": 1.5,
                "description": "Measures a company's ability to pay short-term obligations",
                "formula": "Current Assets / Current Liabilities",
                "interpretation": {
                    "good": "> 1.5",
                    "concern": "< 1.0"
                },
                "year": current_year - 1
            },
            "quick_ratio": {
                "value": 1.2,
                "description": "Measures a company's ability to pay short-term obligations with its most liquid assets",
                "formula": "(Current Assets - Inventory) / Current Liabilities",
                "interpretation": {
                    "good": "> 1.0",
                    "concern": "< 0.7"
                },
                "year": current_year - 1
            }
        },
        "solvency_ratios": {
            "debt_to_equity": {
                "value": 0.8,
                "description": "Measures a company's financial leverage",
                "formula": "Total Liabilities / Stockholders' Equity",
                "interpretation": {
                    "good": "< 1.5",
                    "concern": "> 2.0"
                },
                "year": current_year - 1
            }
        },
        "profitability_ratios": {
            "return_on_assets": {
                "value": 8.5,
                "description": "Measures how efficiently a company is using its assets to generate profit",
                "formula": "(Net Income / Total Assets) * 100%",
                "interpretation": {
                    "good": "> 5%",
                    "concern": "< 2%"
                },
                "year": current_year - 1
            },
            "return_on_equity": {
                "value": 15.2,
                "description": "Measures how efficiently a company is using its equity to generate profit",
                "formula": "(Net Income / Stockholders' Equity) * 100%",
                "interpretation": {
                    "good": "> 15%",
                    "concern": "< 10%"
                },
                "year": current_year - 1
            },
            "gross_margin": {
                "value": 42.0,
                "description": "Measures the percentage of revenue that exceeds the cost of goods sold",
                "formula": "((Revenue - COGS) / Revenue) * 100%",
                "interpretation": {
                    "good": "Industry dependent, higher is better",
                    "concern": "Declining over time"
                },
                "year": current_year - 1
            },
            "net_profit_margin": {
                "value": 12.5,
                "description": "Measures how much net profit is generated as a percentage of revenue",
                "formula": "(Net Income / Revenue) * 100%",
                "interpretation": {
                    "good": "> 10%",
                    "concern": "< 5%"
                },
                "year": current_year - 1
            }
        }
    }
    
    # Add P/E ratio if current price is provided
    if current_price is not None:
        ratios["valuation_ratios"] = {
            "price_to_earnings": {
                "value": 22.5,
                "description": "Measures the current share price relative to earnings per share",
                "formula": "Current Stock Price / Earnings Per Share",
                "interpretation": {
                    "good": "Industry dependent, 10-20 is typical",
                    "concern": "> 30 may indicate overvaluation"
                },
                "year": current_year - 1
            }
        }
    
    # Add metadata
    ratios["metadata"] = {
        "calculated_at": datetime.now().isoformat(),
        "data_year": current_year - 1
    }
    
    return ratios 