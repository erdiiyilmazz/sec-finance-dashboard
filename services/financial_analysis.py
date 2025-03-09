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