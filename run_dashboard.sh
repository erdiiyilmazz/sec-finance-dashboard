#!/bin/bash

# SEC Dashboard Runner Script
# This script provides a unified way to run different components of the SEC Dashboard

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    
    # Construct the user agent from environment variables
    if [ -n "$SEC_API_NAME" ] && [ -n "$SEC_API_EMAIL" ] && [ -n "$SEC_API_PHONE" ]; then
        export SEC_API_USER_AGENT="$SEC_API_NAME ($SEC_API_EMAIL, $SEC_API_PHONE)"
    else
        # Fallback to a generic user agent if environment variables are not set
        export SEC_API_USER_AGENT="SEC Dashboard (contact@example.com)"
    fi
else
    echo "Warning: .env file not found. Using default values."
    export SEC_API_USER_AGENT="SEC Dashboard (contact@example.com)"
fi

echo "Using User-Agent: $SEC_API_USER_AGENT"

# Function to display usage information
show_usage() {
    echo "SEC Dashboard Runner"
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help                 Show this help message"
    echo "  --simple-api           Run only the simple API (port 8001)"
    echo "  --complex-api          Run only the complex API (port 8000)"
    echo "  --both-apis            Run both APIs (simple on 8001, complex on 8000)"
    echo "  --dashboard            Run the dashboard HTTP server (port 8080)"
    echo "  --all                  Run both APIs and the dashboard (default)"
    echo ""
    echo "Examples:"
    echo "  $0                     Run everything (both APIs and dashboard)"
    echo "  $0 --simple-api        Run only the simple API"
    echo "  $0 --dashboard         Run only the dashboard"
    echo ""
}

# Function to run the simple API
run_simple_api() {
    echo "Starting simple API server on port 8001..."
    pkill -f "python simple_api.py" || true
    python simple_api.py > simple_api_logs.txt 2>&1 &
    SIMPLE_API_PID=$!
    
    # Wait for the API to start
    echo "Waiting for simple API to start..."
    sleep 2
    
    # Check if the API is running
    if curl -s http://localhost:8001/ > /dev/null; then
        echo "Simple API server started successfully (PID: $SIMPLE_API_PID)"
        return 0
    else
        echo "Error: Simple API failed to start. Check simple_api_logs.txt for details."
        return 1
    fi
}

# Function to run the complex API
run_complex_api() {
    echo "Starting complex API server on port 8000..."
    pkill -f "python main.py" || true
    python main.py --component api --api-host 0.0.0.0 --api-port 8000 > complex_api_logs.txt 2>&1 &
    COMPLEX_API_PID=$!
    
    # Wait for the API to start
    echo "Waiting for complex API to start..."
    sleep 3
    
    # Check if the API is running
    if curl -s http://localhost:8000/ > /dev/null; then
        echo "Complex API server started successfully (PID: $COMPLEX_API_PID)"
        return 0
    else
        echo "Error: Complex API failed to start. Check complex_api_logs.txt for details."
        return 1
    fi
}

# Function to run the dashboard
run_dashboard() {
    echo "Starting dashboard server on port 8080..."
    pkill -f "python serve_dashboard.py" || true
    python serve_dashboard.py > dashboard_logs.txt 2>&1 &
    DASHBOARD_PID=$!
    
    # Wait for the dashboard server to start
    echo "Waiting for dashboard server to start..."
    sleep 2
    
    echo "Dashboard server started successfully (PID: $DASHBOARD_PID)"
    echo "Dashboard is available at: http://localhost:8080/simple_dashboard.html"
    return 0
}

# Store PIDs for cleanup message
PIDS=()

# Parse command line arguments
if [ $# -eq 0 ]; then
    # Default: run everything
    run_simple_api
    PIDS+=($SIMPLE_API_PID)
    run_dashboard
    PIDS+=($DASHBOARD_PID)
else
    case "$1" in
        --help)
            show_usage
            exit 0
            ;;
        --simple-api)
            run_simple_api
            PIDS+=($SIMPLE_API_PID)
            ;;
        --complex-api)
            run_complex_api
            PIDS+=($COMPLEX_API_PID)
            ;;
        --both-apis)
            run_simple_api
            PIDS+=($SIMPLE_API_PID)
            run_complex_api
            PIDS+=($COMPLEX_API_PID)
            ;;
        --dashboard)
            run_dashboard
            PIDS+=($DASHBOARD_PID)
            ;;
        --all)
            run_simple_api
            PIDS+=($SIMPLE_API_PID)
            run_complex_api
            PIDS+=($COMPLEX_API_PID)
            run_dashboard
            PIDS+=($DASHBOARD_PID)
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
fi

# Print cleanup instructions
if [ ${#PIDS[@]} -gt 0 ]; then
    echo "Done! To stop the servers, run: kill ${PIDS[@]}"
fi 