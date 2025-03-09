import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime
import json


# API URL (change this to your actual API URL when deployed)
API_URL = "http://127.0.0.1:8000"


# Page configuration
st.set_page_config(
    page_title="SEC Filings Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Helper functions
def format_number(num):
    """Format a number with commas and 2 decimal places."""
    if num is None:
        return "N/A"
    
    if abs(num) >= 1e9:
        return f"${num/1e9:.2f}B"
    elif abs(num) >= 1e6:
        return f"${num/1e6:.2f}M"
    elif abs(num) >= 1e3:
        return f"${num/1e3:.2f}K"
    else:
        return f"${num:.2f}"


def format_percentage(num):
    """Format a number as a percentage."""
    if num is None:
        return "N/A"
    
    return f"{num*100:.2f}%"


def get_companies():
    """Get a list of companies from the API."""
    try:
        response = requests.get(f"{API_URL}/companies/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching companies: {e}")
        return []


def get_company(ticker):
    """Get company details from the API."""
    try:
        response = requests.get(f"{API_URL}/companies/{ticker}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching company {ticker}: {e}")
        return None


def get_company_metric(ticker, metric_name, period="annual"):
    """Get a specific financial metric for a company."""
    try:
        response = requests.get(
            f"{API_URL}/companies/{ticker}/metrics/{metric_name}",
            params={"period": period}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching {metric_name} for {ticker}: {e}")
        return None


def get_company_ratios(ticker):
    """Get financial ratios for a company."""
    try:
        response = requests.get(f"{API_URL}/companies/{ticker}/ratios")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching ratios for {ticker}: {e}")
        return None


def compare_companies(tickers, metric_name):
    """Compare multiple companies based on a specific metric."""
    try:
        response = requests.get(
            f"{API_URL}/companies/compare/{metric_name}",
            params={"tickers": ",".join(tickers)}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error comparing companies: {e}")
        return None


def sync_company_data(ticker, force_refresh=False):
    """Synchronize company data with the SEC API."""
    try:
        response = requests.post(
            f"{API_URL}/companies/{ticker}/sync",
            params={"force_refresh": force_refresh}
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error syncing data for {ticker}: {e}")
        return None


# Check if we should redirect to Data Sync page
if 'redirect_to_data_sync' in st.session_state and st.session_state.redirect_to_data_sync:
    st.session_state.redirect_to_data_sync = False
    st.session_state.page = "Data Sync"

# Initialize session state for page if not exists
if 'page' not in st.session_state:
    st.session_state.page = "Company Explorer"

# Sidebar
st.sidebar.title("SEC Filings Dashboard")
st.sidebar.markdown("Explore financial data from SEC filings")

# Navigation
page = st.sidebar.selectbox(
    "Select a page",
    ["Company Explorer", "Metric Comparison", "Data Sync"],
    index=["Company Explorer", "Metric Comparison", "Data Sync"].index(st.session_state.page)
)

# Update session state
st.session_state.page = page

# Company Explorer page
if page == "Company Explorer":
    st.title("Company Explorer")
    
    # Get companies
    companies = get_companies()
    
    if not companies:
        st.warning("No companies found. Please sync some data first.")
        st.info("Click the button below to go to the Data Sync page and add a company.")
        
        if st.button("Go to Data Sync Page"):
            st.session_state.page = "Data Sync"
            st.experimental_rerun()
    else:
        # Convert to DataFrame for easier filtering
        df_companies = pd.DataFrame(companies)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            if "sector" in df_companies.columns and not df_companies["sector"].isna().all():
                selected_sector = st.selectbox(
                    "Filter by sector",
                    ["All"] + sorted(df_companies["sector"].dropna().unique().tolist())
                )
            else:
                selected_sector = "All"
                
        with col2:
            if "industry" in df_companies.columns and not df_companies["industry"].isna().all():
                selected_industry = st.selectbox(
                    "Filter by industry",
                    ["All"] + sorted(df_companies["industry"].dropna().unique().tolist())
                )
            else:
                selected_industry = "All"
        
        # Apply filters
        filtered_df = df_companies.copy()
        if selected_sector != "All":
            filtered_df = filtered_df[filtered_df["sector"] == selected_sector]
        if selected_industry != "All":
            filtered_df = filtered_df[filtered_df["industry"] == selected_industry]
        
        # Company selection
        selected_ticker = st.selectbox(
            "Select a company",
            sorted(filtered_df["ticker"].tolist()),
            format_func=lambda x: f"{x} - {filtered_df[filtered_df['ticker'] == x]['name'].values[0]}"
        )
        
        # Get company details
        company = get_company(selected_ticker)
        
        if company:
            # Company info
            col1, col2 = st.columns(2)
            with col1:
                st.subheader(f"{company['name']} ({company['ticker']})")
                st.markdown(f"**CIK:** {company['cik']}")
                if company.get('sector'):
                    st.markdown(f"**Sector:** {company['sector']}")
                if company.get('industry'):
                    st.markdown(f"**Industry:** {company['industry']}")
                if company.get('website'):
                    st.markdown(f"**Website:** [{company['website']}]({company['website']})")
            
            # Financial metrics
            st.subheader("Financial Metrics")
            
            # Metric selection
            metric_options = [
                "Revenue", "NetIncome", "TotalAssets", "TotalLiabilities",
                "OperatingIncome", "EPS", "CashAndEquivalents", "StockholdersEquity"
            ]
            selected_metric = st.selectbox("Select a metric", metric_options)
            
            # Period selection
            period_options = ["annual", "quarterly"]
            selected_period = st.radio("Select period", period_options, horizontal=True)
            
            # Get metric data
            metric_data = get_company_metric(selected_ticker, selected_metric, selected_period)
            
            if metric_data and metric_data.get("time_series"):
                # Convert to DataFrame
                df_metric = pd.DataFrame([
                    {"date": datetime.fromisoformat(item["date"]), "value": item["value"]}
                    for item in metric_data["time_series"]
                ])
                
                # Sort by date
                df_metric = df_metric.sort_values("date")
                
                # Create chart
                fig = px.line(
                    df_metric, 
                    x="date", 
                    y="value",
                    title=f"{selected_metric} ({selected_period})",
                    labels={"date": "Date", "value": "Value"},
                )
                
                # Format y-axis as currency
                fig.update_layout(
                    yaxis=dict(
                        tickprefix="$",
                        tickformat=",.0f",
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Growth rates
                if metric_data.get("growth_rates"):
                    st.subheader("Growth Rates")
                    
                    # Convert to DataFrame
                    df_growth = pd.DataFrame([
                        {"date": datetime.fromisoformat(item["date"]), "rate": item["rate"]}
                        for item in metric_data["growth_rates"]
                    ])
                    
                    # Sort by date
                    df_growth = df_growth.sort_values("date")
                    
                    # Create chart
                    fig = px.bar(
                        df_growth, 
                        x="date", 
                        y="rate",
                        title=f"{selected_metric} Growth Rate ({selected_period})",
                        labels={"date": "Date", "rate": "Growth Rate"},
                    )
                    
                    # Format y-axis as percentage
                    fig.update_layout(
                        yaxis=dict(
                            tickformat=".1%",
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                # CAGR
                if selected_period == "annual" and metric_data.get("cagr") is not None:
                    st.metric(
                        "Compound Annual Growth Rate (CAGR)",
                        format_percentage(metric_data["cagr"])
                    )
            else:
                st.warning(f"No {selected_metric} data available for {selected_ticker}")
            
            # Financial ratios
            st.subheader("Financial Ratios")
            ratios = get_company_ratios(selected_ticker)
            
            if ratios:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if "ROA" in ratios:
                        st.metric("Return on Assets (ROA)", format_percentage(ratios["ROA"]))
                
                with col2:
                    if "ROE" in ratios:
                        st.metric("Return on Equity (ROE)", format_percentage(ratios["ROE"]))
                
                with col3:
                    if "DebtToEquity" in ratios:
                        st.metric("Debt to Equity", f"{ratios['DebtToEquity']:.2f}")
                
                with col4:
                    if "ProfitMargin" in ratios:
                        st.metric("Profit Margin", format_percentage(ratios["ProfitMargin"]))
            else:
                st.warning(f"No financial ratio data available for {selected_ticker}")

# Metric Comparison page
elif page == "Metric Comparison":
    st.title("Metric Comparison")
    
    # Get companies
    companies = get_companies()
    
    if not companies:
        st.warning("No companies found. Please sync some data first.")
        st.info("Click the button below to go to the Data Sync page and add a company.")
        
        if st.button("Go to Data Sync Page"):
            st.session_state.page = "Data Sync"
            st.experimental_rerun()
    else:
        # Convert to DataFrame for easier filtering
        df_companies = pd.DataFrame(companies)
        
        # Metric selection
        metric_options = [
            "Revenue", "NetIncome", "TotalAssets", "TotalLiabilities",
            "OperatingIncome", "EPS", "CashAndEquivalents", "StockholdersEquity"
        ]
        selected_metric = st.selectbox("Select a metric to compare", metric_options)
        
        # Company selection
        selected_tickers = st.multiselect(
            "Select companies to compare",
            sorted(df_companies["ticker"].tolist()),
            format_func=lambda x: f"{x} - {df_companies[df_companies['ticker'] == x]['name'].values[0]}"
        )
        
        if selected_tickers:
            # Compare companies
            comparison_data = compare_companies(selected_tickers, selected_metric)
            
            if comparison_data:
                # Latest values
                st.subheader(f"Latest {selected_metric} Values")
                
                # Create DataFrame for latest values
                latest_data = []
                for ticker, data in comparison_data.items():
                    latest_data.append({
                        "ticker": ticker,
                        "company_name": data["company_name"],
                        "value": data["latest_value"],
                        "date": datetime.fromisoformat(data["latest_date"]) if data["latest_date"] else None,
                        "growth_rate": data["growth_rate"],
                        "cagr": data["cagr"]
                    })
                
                df_latest = pd.DataFrame(latest_data)
                
                # Sort by value
                df_latest = df_latest.sort_values("value", ascending=False)
                
                # Create bar chart
                fig = px.bar(
                    df_latest,
                    x="ticker",
                    y="value",
                    title=f"Latest {selected_metric} Values",
                    labels={"ticker": "Company", "value": "Value"},
                    hover_data=["company_name", "date"],
                    color="ticker"
                )
                
                # Format y-axis as currency
                fig.update_layout(
                    yaxis=dict(
                        tickprefix="$",
                        tickformat=",.0f",
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Growth rates
                st.subheader(f"{selected_metric} Growth Rates")
                
                # Create DataFrame for growth rates
                growth_data = []
                for ticker, data in comparison_data.items():
                    if data["growth_rate"] is not None:
                        growth_data.append({
                            "ticker": ticker,
                            "company_name": data["company_name"],
                            "growth_rate": data["growth_rate"]
                        })
                
                if growth_data:
                    df_growth = pd.DataFrame(growth_data)
                    
                    # Sort by growth rate
                    df_growth = df_growth.sort_values("growth_rate", ascending=False)
                    
                    # Create bar chart
                    fig = px.bar(
                        df_growth,
                        x="ticker",
                        y="growth_rate",
                        title=f"{selected_metric} Growth Rates",
                        labels={"ticker": "Company", "growth_rate": "Growth Rate"},
                        hover_data=["company_name"],
                        color="ticker"
                    )
                    
                    # Format y-axis as percentage
                    fig.update_layout(
                        yaxis=dict(
                            tickformat=".1%",
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No growth rate data available for the selected companies")
                
                # Time series comparison
                st.subheader(f"{selected_metric} Time Series Comparison")
                
                # Create DataFrame for time series
                time_series_data = []
                for ticker, data in comparison_data.items():
                    for ts_point in data["time_series"]:
                        time_series_data.append({
                            "ticker": ticker,
                            "company_name": data["company_name"],
                            "date": datetime.fromisoformat(ts_point["date"]),
                            "value": ts_point["value"]
                        })
                
                df_ts = pd.DataFrame(time_series_data)
                
                # Create line chart
                fig = px.line(
                    df_ts,
                    x="date",
                    y="value",
                    color="ticker",
                    title=f"{selected_metric} Time Series Comparison",
                    labels={"date": "Date", "value": "Value", "ticker": "Company"},
                    hover_data=["company_name"]
                )
                
                # Format y-axis as currency
                fig.update_layout(
                    yaxis=dict(
                        tickprefix="$",
                        tickformat=",.0f",
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No comparison data available for the selected companies and metric")
        else:
            st.info("Please select at least one company to compare")

# Data Sync page
elif page == "Data Sync":
    st.title("Data Synchronization")
    
    st.markdown("""
    This page allows you to synchronize company data with the SEC API.
    
    1. Enter a ticker symbol
    2. Click "Sync Data"
    3. Wait for the synchronization to complete
    """)
    
    # Ticker input
    ticker = st.text_input("Enter ticker symbol", "").upper()
    
    # Force refresh option
    force_refresh = st.checkbox("Force refresh (ignore cache)")
    
    # Sync button
    if st.button("Sync Data"):
        if ticker:
            with st.spinner(f"Syncing data for {ticker}..."):
                result = sync_company_data(ticker, force_refresh)
                
                if result:
                    st.success(f"Successfully synchronized data for {result['name']} ({result['ticker']})")
                    st.json(result)
                    
                    # Add a button to view the company
                    if st.button("View Company Data"):
                        st.session_state.page = "Company Explorer"
                        st.experimental_rerun()
                else:
                    st.error(f"Failed to synchronize data for {ticker}")
        else:
            st.warning("Please enter a ticker symbol") 