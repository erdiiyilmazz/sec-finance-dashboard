from typing import List, Optional, Dict, Any, Tuple
import json
import os
from datetime import datetime

from models.financial_metric import FinancialMetric, MetricPeriod
from repositories.base_repository import BaseRepository


class FinancialMetricRepository(BaseRepository[FinancialMetric]):
    """
    Repository for managing financial metrics.
    """
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the repository with a data directory."""
        self.data_dir = data_dir
        self.metrics_dir = os.path.join(data_dir, "metrics")
        self.metrics: Dict[str, FinancialMetric] = {}  # metric_id -> FinancialMetric
        
        # Create directories if they don't exist
        os.makedirs(self.metrics_dir, exist_ok=True)
        
        # Load metrics from files
        self._load_metrics()
    
    def get_by_id(self, id: str) -> Optional[FinancialMetric]:
        """Get a metric by its ID."""
        return self.metrics.get(id)
    
    def get_all(self) -> List[FinancialMetric]:
        """Get all metrics."""
        return list(self.metrics.values())
    
    def create(self, metric: FinancialMetric) -> FinancialMetric:
        """Create a new metric."""
        # Generate a unique ID for the metric
        metric_id = self._generate_metric_id(metric)
        
        if metric_id in self.metrics:
            raise ValueError(f"Metric with ID {metric_id} already exists")
        
        self.metrics[metric_id] = metric
        self._save_metric(metric_id, metric)
        return metric
    
    def update(self, metric: FinancialMetric) -> FinancialMetric:
        """Update an existing metric."""
        metric_id = self._generate_metric_id(metric)
        
        if metric_id not in self.metrics:
            raise ValueError(f"Metric with ID {metric_id} does not exist")
        
        self.metrics[metric_id] = metric
        self._save_metric(metric_id, metric)
        return metric
    
    def delete(self, id: str) -> bool:
        """Delete a metric by its ID."""
        if id in self.metrics:
            del self.metrics[id]
            
            # Delete the metric file
            metric_path = self._get_metric_path(id)
            if os.path.exists(metric_path):
                os.remove(metric_path)
            
            return True
        return False
    
    def find_by(self, criteria: Dict[str, Any]) -> List[FinancialMetric]:
        """Find metrics matching the given criteria."""
        results = []
        
        for metric in self.metrics.values():
            match = True
            for key, value in criteria.items():
                if not hasattr(metric, key) or getattr(metric, key) != value:
                    match = False
                    break
            
            if match:
                results.append(metric)
        
        return results
    
    def find_by_company_id(self, company_id: str) -> List[FinancialMetric]:
        """Find metrics for a specific company."""
        return [m for m in self.metrics.values() if m.company_id == company_id]
    
    def find_by_filing_id(self, filing_id: str) -> List[FinancialMetric]:
        """Find metrics from a specific filing."""
        return [m for m in self.metrics.values() if m.filing_id == filing_id]
    
    def find_by_name(self, name: str) -> List[FinancialMetric]:
        """Find metrics with a specific name."""
        return [m for m in self.metrics.values() if m.name == name]
    
    def find_by_name_and_period(self, name: str, period: MetricPeriod) -> List[FinancialMetric]:
        """Find metrics with a specific name and period."""
        return [
            m for m in self.metrics.values() 
            if m.name == name and m.period == period
        ]
    
    def find_by_company_and_metric(self, company_id: str, metric_name: str, 
                                  period: MetricPeriod = None) -> List[FinancialMetric]:
        """Find metrics for a specific company and metric name."""
        results = [
            m for m in self.metrics.values() 
            if m.company_id == company_id and m.name == metric_name
        ]
        
        if period:
            results = [m for m in results if m.period == period]
            
        return results
    
    def get_time_series(self, company_id: str, metric_name: str, 
                        period: MetricPeriod) -> List[Tuple[datetime, float]]:
        """Get a time series of values for a specific metric."""
        metrics = self.find_by_company_and_metric(company_id, metric_name, period)
        
        # Sort by date
        metrics.sort(key=lambda m: m.date)
        
        # Return as (date, value) pairs
        return [(m.date, m.value) for m in metrics]
    
    def _generate_metric_id(self, metric: FinancialMetric) -> str:
        """Generate a unique ID for a metric."""
        components = [
            metric.company_id or "unknown",
            metric.name,
            metric.period.value if isinstance(metric.period, MetricPeriod) else str(metric.period),
            metric.date.isoformat()
        ]
        
        return "_".join(components)
    
    def _get_metric_path(self, metric_id: str) -> str:
        """Get the file path for a metric."""
        return os.path.join(self.metrics_dir, f"{metric_id}.json")
    
    def _save_metric(self, metric_id: str, metric: FinancialMetric) -> None:
        """Save a metric to a JSON file."""
        metric_data = {
            "name": metric.name,
            "value": metric.value,
            "date": metric.date.isoformat(),
            "period": metric.period.value if isinstance(metric.period, MetricPeriod) else metric.period,
            "unit": metric.unit,
            "decimals": metric.decimals,
            "filing_id": metric.filing_id,
            "company_id": metric.company_id,
            "xbrl_tag": metric.xbrl_tag,
            "xbrl_context": metric.xbrl_context,
            "is_calculated": metric.is_calculated,
            "calculation_method": metric.calculation_method,
            "confidence_score": metric.confidence_score
        }
        
        metric_path = self._get_metric_path(metric_id)
        with open(metric_path, 'w') as f:
            json.dump(metric_data, f, indent=2)
    
    def _load_metrics(self) -> None:
        """Load all metrics from JSON files."""
        for filename in os.listdir(self.metrics_dir):
            if filename.endswith('.json'):
                metric_path = os.path.join(self.metrics_dir, filename)
                with open(metric_path, 'r') as f:
                    metric_data = json.load(f)
                
                # Convert ISO format date string to datetime
                date = datetime.fromisoformat(metric_data["date"])
                
                # Convert period string to MetricPeriod enum
                period = MetricPeriod(metric_data["period"])
                
                metric = FinancialMetric(
                    name=metric_data["name"],
                    value=metric_data["value"],
                    date=date,
                    period=period,
                    unit=metric_data.get("unit", "USD"),
                    decimals=metric_data.get("decimals"),
                    filing_id=metric_data.get("filing_id"),
                    xbrl_tag=metric_data.get("xbrl_tag"),
                    xbrl_context=metric_data.get("xbrl_context"),
                    company_id=metric_data.get("company_id"),
                    is_calculated=metric_data.get("is_calculated", False),
                    calculation_method=metric_data.get("calculation_method"),
                    confidence_score=metric_data.get("confidence_score")
                )
                
                metric_id = self._generate_metric_id(metric)
                self.metrics[metric_id] = metric 