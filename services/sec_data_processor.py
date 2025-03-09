from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from models.company import Company
from models.filing import Filing
from models.financial_metric import FinancialMetric, MetricPeriod
from models.cik_ticker_mapping import CIKTickerMapping
from repositories.company_repository import CompanyRepository
from repositories.filing_repository import FilingRepository
from repositories.financial_metric_repository import FinancialMetricRepository
from repositories.cik_ticker_repository import CIKTickerRepository
from services.sec_api_service import SECAPIService


class SECDataProcessor:
    """
    Service for processing SEC data and extracting financial metrics.
    """
    
    # Common financial metrics to extract
    COMMON_METRICS = {
        "Revenue": ["Revenue", "Revenues", "SalesRevenueNet", "SalesRevenueGoodsNet"],
        "NetIncome": ["NetIncomeLoss", "ProfitLoss"],
        "TotalAssets": ["Assets"],
        "TotalLiabilities": ["Liabilities"],
        "OperatingIncome": ["OperatingIncomeLoss"],
        "EPS": ["EarningsPerShareBasic", "EarningsPerShareDiluted"],
        "CashAndEquivalents": ["CashAndCashEquivalentsAtCarryingValue"],
        "Goodwill": ["Goodwill"],
        "RetainedEarnings": ["RetainedEarningsAccumulatedDeficit"],
        "StockholdersEquity": ["StockholdersEquity"]
    }
    
    def __init__(self, 
                 sec_api_service: SECAPIService,
                 company_repository: CompanyRepository,
                 filing_repository: FilingRepository,
                 metric_repository: FinancialMetricRepository,
                 cik_ticker_repository: CIKTickerRepository):
        """
        Initialize the SEC data processor.
        
        Args:
            sec_api_service: Service for interacting with the SEC API
            company_repository: Repository for managing companies
            filing_repository: Repository for managing filings
            metric_repository: Repository for managing financial metrics
            cik_ticker_repository: Repository for managing CIK-ticker mappings
        """
        self.sec_api = sec_api_service
        self.company_repo = company_repository
        self.filing_repo = filing_repository
        self.metric_repo = metric_repository
        self.cik_ticker_repo = cik_ticker_repository
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def sync_cik_ticker_mappings(self, force_refresh: bool = False) -> List[CIKTickerMapping]:
        """
        Synchronize CIK-ticker mappings with the SEC API.
        
        Args:
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            List of CIK-ticker mappings
        """
        # Get company tickers from SEC API
        company_tickers = self.sec_api.get_company_tickers(force_refresh=force_refresh)
        
        # Create or update CIK-ticker mappings
        mappings = []
        
        # Handle the new format from the SEC API
        if "data" in company_tickers:
            # New format with 'data' key
            ticker_data = company_tickers["data"]
            for item in ticker_data:
                cik = str(item.get("cik", "")).zfill(10)
                ticker = item.get("ticker", "")
                company_name = item.get("name", "")
                exchange = item.get("exchange", "")
                
                if not cik or not ticker:
                    continue
                
                # Check if mapping already exists
                existing_mapping = self.cik_ticker_repo.get_by_cik(cik)
                
                if existing_mapping:
                    # Update existing mapping
                    existing_mapping.ticker = ticker
                    existing_mapping.company_name = company_name
                    existing_mapping.exchange = exchange
                    existing_mapping.last_updated = datetime.now()
                    self.cik_ticker_repo.update(existing_mapping)
                    mappings.append(existing_mapping)
                else:
                    # Create new mapping
                    new_mapping = CIKTickerMapping(
                        cik=cik,
                        ticker=ticker,
                        company_name=company_name,
                        exchange=exchange,
                        last_updated=datetime.now()
                    )
                    self.cik_ticker_repo.create(new_mapping)
                    mappings.append(new_mapping)
        else:
            # Old format (direct dictionary)
            for cik, company_info in company_tickers.items():
                # Check if mapping already exists
                existing_mapping = self.cik_ticker_repo.get_by_cik(cik)
                
                if existing_mapping:
                    # Update existing mapping
                    existing_mapping.ticker = company_info["ticker"]
                    existing_mapping.company_name = company_info["title"]
                    existing_mapping.last_updated = datetime.now()
                    self.cik_ticker_repo.update(existing_mapping)
                    mappings.append(existing_mapping)
                else:
                    # Create new mapping
                    new_mapping = CIKTickerMapping(
                        cik=cik,
                        ticker=company_info["ticker"],
                        company_name=company_info["title"],
                        last_updated=datetime.now()
                    )
                    self.cik_ticker_repo.create(new_mapping)
                    mappings.append(new_mapping)
        
        self.logger.info(f"Synchronized {len(mappings)} CIK-ticker mappings")
        return mappings
    
    def sync_company_data(self, ticker: str, force_refresh: bool = False) -> Optional[Company]:
        """
        Synchronize company data with the SEC API.
        
        Args:
            ticker: Ticker symbol of the company
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            Company object if successful, None otherwise
        """
        # Get CIK for ticker
        mapping = self.cik_ticker_repo.get_by_ticker(ticker)
        if not mapping:
            self.logger.error(f"No CIK mapping found for ticker {ticker}")
            return None
        
        # Get company submissions from SEC API
        submissions = self.sec_api.get_company_submissions(mapping.cik, force_refresh=force_refresh)
        
        # Check if company exists
        company = self.company_repo.get_by_ticker(ticker)
        
        if company:
            # Update existing company
            company.name = mapping.company_name
            company.cik = mapping.cik
            self.company_repo.update(company)
        else:
            # Create new company
            company = Company(
                ticker=ticker,
                name=mapping.company_name,
                cik=mapping.cik
            )
            self.company_repo.create(company)
        
        # Process recent filings
        self._process_company_filings(company, submissions, force_refresh)
        
        # Process financial metrics
        self._process_company_metrics(company, force_refresh)
        
        return company
    
    def _process_company_filings(self, company: Company, submissions: Dict[str, Any], 
                                force_refresh: bool = False) -> List[Filing]:
        """
        Process company filings from SEC submissions data.
        
        Args:
            company: Company object
            submissions: SEC submissions data
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            List of processed filings
        """
        filings = []
        
        # Get recent filings (10-K, 10-Q)
        recent_filings = submissions.get("filings", {}).get("recent", {})
        
        if not recent_filings:
            self.logger.warning(f"No recent filings found for {company.ticker}")
            return filings
        
        # Extract filing data
        accession_numbers = recent_filings.get("accessionNumber", [])
        form_types = recent_filings.get("form", [])
        filing_dates = recent_filings.get("filingDate", [])
        reporting_dates = recent_filings.get("reportDate", [])
        
        # Process each filing
        for i in range(len(accession_numbers)):
            # Only process 10-K and 10-Q filings
            if form_types[i] not in ["10-K", "10-Q"]:
                continue
            
            # Check if filing already exists
            existing_filing = self.filing_repo.get_by_id(accession_numbers[i])
            
            if existing_filing and not force_refresh:
                filings.append(existing_filing)
                continue
            
            # Parse dates
            filing_date = datetime.strptime(filing_dates[i], "%Y-%m-%d")
            period_end_date = datetime.strptime(reporting_dates[i], "%Y-%m-%d")
            
            # Create or update filing
            if existing_filing:
                existing_filing.filing_date = filing_date
                existing_filing.period_end_date = period_end_date
                existing_filing.company_id = company.ticker
                existing_filing.company = company
                self.filing_repo.update(existing_filing)
                filings.append(existing_filing)
            else:
                new_filing = Filing(
                    accession_number=accession_numbers[i],
                    form_type=form_types[i],
                    filing_date=filing_date,
                    period_end_date=period_end_date,
                    company_id=company.ticker,
                    company=company
                )
                self.filing_repo.create(new_filing)
                filings.append(new_filing)
        
        self.logger.info(f"Processed {len(filings)} filings for {company.ticker}")
        return filings
    
    def _process_company_metrics(self, company: Company, force_refresh: bool = False) -> List[FinancialMetric]:
        """
        Process financial metrics for a company.
        
        Args:
            company: Company object
            force_refresh: Whether to force a refresh from the SEC API
            
        Returns:
            List of processed financial metrics
        """
        metrics = []
        
        # Get company facts from SEC API
        try:
            facts = self.sec_api.get_company_facts(company.cik, force_refresh=force_refresh)
        except Exception as e:
            self.logger.error(f"Error fetching facts for {company.ticker}: {e}")
            return metrics
        
        # Extract US GAAP facts
        us_gaap = facts.get("facts", {}).get("us-gaap", {})
        
        if not us_gaap:
            self.logger.warning(f"No US GAAP facts found for {company.ticker}")
            return metrics
        
        # Process each common metric
        for metric_name, possible_tags in self.COMMON_METRICS.items():
            # Find the first available tag
            for tag in possible_tags:
                if tag in us_gaap:
                    self._process_metric_tag(company, metric_name, tag, us_gaap[tag], metrics)
                    break
        
        self.logger.info(f"Processed {len(metrics)} metrics for {company.ticker}")
        return metrics
    
    def _process_metric_tag(self, company: Company, metric_name: str, xbrl_tag: str, 
                           tag_data: Dict[str, Any], metrics_list: List[FinancialMetric]) -> None:
        """
        Process a specific XBRL tag and extract financial metrics.
        
        Args:
            company: Company object
            metric_name: Standardized metric name
            xbrl_tag: XBRL tag name
            tag_data: Tag data from SEC API
            metrics_list: List to append extracted metrics to
        """
        # Get units and values
        units = tag_data.get("units", {})
        
        # Most financial values are in USD
        if "USD" in units:
            values = units["USD"]
        # Some might be pure numbers (like EPS)
        elif "pure" in units:
            values = units["pure"]
        else:
            self.logger.warning(f"No supported units found for {company.ticker} {metric_name}")
            return
        
        # Process each value
        for value_data in values:
            # Extract data
            val = value_data.get("val")
            if val is None:
                continue
                
            end_date = value_data.get("end")
            if not end_date:
                continue
                
            # Parse date
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
            
            # Determine period type
            period = None
            if "frame" in value_data:
                frame = value_data["frame"]
                if "Q" in frame:
                    period = MetricPeriod.QUARTERLY
                elif "Y" in frame:
                    period = MetricPeriod.ANNUAL
                else:
                    period = MetricPeriod.ANNUAL  # Default to annual if unclear
            else:
                # Try to infer from context
                fy_end = value_data.get("fy")
                fp = value_data.get("fp")
                
                if fp == "FY":
                    period = MetricPeriod.ANNUAL
                elif fp in ["Q1", "Q2", "Q3", "Q4"]:
                    period = MetricPeriod.QUARTERLY
                else:
                    period = MetricPeriod.ANNUAL  # Default to annual if unclear
            
            # Create metric
            metric = FinancialMetric(
                name=metric_name,
                value=val,
                date=end_date,
                period=period,
                xbrl_tag=xbrl_tag,
                xbrl_context=value_data.get("accn"),
                company_id=company.ticker
            )
            
            # Add to repository
            try:
                self.metric_repo.create(metric)
                metrics_list.append(metric)
            except ValueError:
                # Metric already exists, update it
                self.metric_repo.update(metric)
                metrics_list.append(metric) 