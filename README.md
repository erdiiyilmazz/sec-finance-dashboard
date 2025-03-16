# SEC Filings Dashboard

A comprehensive dashboard for viewing and analyzing SEC filings data.

## Project Overview

This project provides a dashboard for viewing and analyzing SEC filings data, with the following capabilities:

* Fetching company information from the SEC EDGAR database
* Viewing company details and filings
* Analyzing financial metrics from 10-K and 10-Q filings
* Comparing financial performance across companies
* Viewing 10-K filings for companies

## Technology Stack

### Backend
* Python 3.8+
* FastAPI
* Requests
* Pandas
* NumPy

### Frontend
* Streamlit
* Simple HTML/CSS/JS Dashboard
* Chart.js
* Bootstrap

## Project Structure

```
sec-filings-dashboard/
├── api/                    # FastAPI application
│   ├── routes/             # API routes
│   ├── dependencies.py     # Dependency injection
│   └── main.py             # API entry point
├── models/                 # Data models
├── repositories/           # Data access layer
├── services/               # Business logic
├── data/                   # Data storage
├── frontend/               # Streamlit frontend
│   └── app.py              # Streamlit application
├── simple_dashboard.html   # Simple HTML/JS dashboard
├── simple_api.py           # Simple FastAPI server
├── serve_dashboard.py      # HTTP server for the dashboard
├── run_dashboard.sh        # Unified script to run components
├── main.py                 # Main application entry point
└── requirements.txt        # Python dependencies
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/sec-filings-dashboard.git
cd sec-filings-dashboard
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the root directory with the following variables:
```
# SEC API Configuration
SEC_API_NAME=SEC Dashboard
SEC_API_EMAIL=your-email@example.com
SEC_API_PHONE=+1-555-123-4567
```

These environment variables are used to construct the User-Agent header for SEC API requests. The SEC requires a User-Agent with contact information in a specific format.

## Running the Application

### Running the Full Application (API + Streamlit)

```bash
python main.py --component both
```

### Running the Simple Dashboard

The simple dashboard provides a lightweight alternative to the Streamlit dashboard.

```bash
# Run everything (both API and dashboard)
./run_dashboard.sh

# Run only the simple API
./run_dashboard.sh --simple-api

# Run only the dashboard
./run_dashboard.sh --dashboard

# Stop all running servers
./run_dashboard.sh --stop

# Show help
./run_dashboard.sh --help
```

The dashboard will be available at: http://localhost:8080/simple_dashboard.html

#### Troubleshooting

If you encounter any issues starting the application:

1. Check if any required dependencies are missing:
   ```bash
   pip install -r requirements.txt
   ```

2. Check if the ports are already in use:
   ```bash
   # Check if port 8001 (API) is in use
   lsof -i:8001
   
   # Check if port 8080 (Dashboard) is in use
   lsof -i:8080
   ```

3. Stop all running servers and start again:
   ```bash
   ./run_dashboard.sh --stop
   ./run_dashboard.sh
   ```

4. Check the log files for errors:
   ```bash
   # Check API logs
   cat simple_api_logs.txt
   
   # Check dashboard logs
   cat dashboard_logs.txt
   ```

5. If you see "Address already in use" errors, stop the servers and try again:
   ```bash
   pkill -f "python simple_api.py"
   pkill -f "python serve_dashboard.py"
   ./run_dashboard.sh
   ```

The improved `run_dashboard.sh` script includes automatic dependency checking, port conflict resolution, and better error handling to help you start the application more reliably.

### About the Improved Dashboard Runner Script

The `run_dashboard.sh` script has been enhanced with several features to make running the application more reliable:

1. **Dependency Checking**: Automatically checks for required Python packages and offers to install them if missing.

2. **Port Conflict Resolution**: Intelligently handles port conflicts by:
   - Detecting if ports are already in use
   - Reusing existing processes if they're responding correctly
   - Attempting to stop conflicting processes if necessary

3. **Better Error Handling**: Provides detailed error information when servers fail to start, including:
   - Showing the last few lines of log files
   - Specific error messages for different failure scenarios
   - Robust checks to verify servers are actually responding

4. **Server Management**: Includes commands to:
   - Start individual components (API, dashboard)
   - Start all components together
   - Stop all running servers

5. **Helpful Instructions**: Provides clear guidance on:
   - How to access the dashboard
   - How to stop the servers
   - What to do if you encounter issues

This script makes it much easier to start, stop, and manage the application, especially when dealing with common issues like port conflicts and missing dependencies.

## Usage

### Simple Dashboard

1. Open the dashboard at http://localhost:8080/simple_dashboard.html
2. Enter a ticker symbol (e.g., AAPL, MSFT, GOOGL) in the search box
3. Click "Get Company Info" to view company details
4. Use the "Limit" dropdown to control how many companies to display
5. Toggle dark mode using the switch in the top-right corner
6. View 10-K filings by clicking on a company and selecting the "View 10-K Filings" button

### Streamlit Dashboard

1. Run the Streamlit dashboard: `python main.py --component frontend`
2. Open the dashboard at http://localhost:8501
3. Use the sidebar to navigate between different views
4. Enter ticker symbols to view company information and filings
5. Compare financial metrics across companies

## Features

- [x] Company information retrieval
- [x] SEC filings display
- [x] Financial metrics extraction
- [x] Dark mode
- [x] Auto-refresh
- [x] 10-K filings access
- [x] Responsive design
- [x] Caching for improved performance
- [ ] Financial statement analysis
- [ ] Export data to CSV/Excel

## Project Roadmap

1. ✅ Basic company information retrieval
2. ✅ SEC filings display
3. ✅ Financial metrics extraction
4. ✅ Simple dashboard
5. ✅ 10-K filings access
6. ⬜ Financial statement analysis
7. ⬜ Advanced visualization

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

* SEC EDGAR database for providing the data
* FastAPI for the API framework
* Streamlit for the dashboard framework 