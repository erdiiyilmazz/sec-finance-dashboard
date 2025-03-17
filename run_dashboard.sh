#!/bin/bash

# SEC Dashboard Runner Script
# This script provides a unified way to run different components of the SEC Dashboard

# Set strict error handling
set -e

# Function to check if a port is in use
check_port_in_use() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        lsof -i:$port >/dev/null 2>&1
        return $?
    elif command -v netstat >/dev/null 2>&1; then
        netstat -an | grep LISTEN | grep :$port >/dev/null 2>&1
        return $?
    else
        # If neither lsof nor netstat is available, try a direct connection
        (echo > /dev/tcp/localhost/$port) >/dev/null 2>&1
        return $?
    fi
}

# Function to check for required Python packages
check_dependencies() {
    echo "Checking for required Python packages..."
    
    # Check if requirements.txt exists
    if [ ! -f "requirements.txt" ]; then
        echo "Warning: requirements.txt not found. Cannot verify dependencies."
        return 0
    fi
    
    # Check for essential packages
    missing_packages=()
    
    for package in python-dotenv fastapi uvicorn requests; do
        if ! python -c "import $(echo $package | tr '-' '_')" >/dev/null 2>&1; then
            missing_packages+=($package)
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo "Missing required Python packages: ${missing_packages[*]}"
        read -p "Would you like to install them now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            pip install -r requirements.txt
            echo "Dependencies installed successfully."
        else
            echo "Warning: Missing dependencies may cause the application to fail."
        fi
    else
        echo "All required Python packages are installed."
    fi
}

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
    echo "  --stop                 Stop all running servers"
    echo ""
    echo "Examples:"
    echo "  $0                     Run everything (both APIs and dashboard)"
    echo "  $0 --simple-api        Run only the simple API"
    echo "  $0 --dashboard         Run only the dashboard"
    echo "  $0 --stop              Stop all running servers"
    echo ""
}

# Function to stop all servers
stop_all_servers() {
    echo "Stopping all running servers..."
    pkill -f "python simple_api.py" 2>/dev/null || true
    pkill -f "python serve_dashboard.py" 2>/dev/null || true
    pkill -f "python main.py" 2>/dev/null || true
    echo "All servers stopped."
}

# Function to run the simple API
run_simple_api() {
    echo "Starting simple API server on port 8001..."
    
    # Check if the port is already in use
    if check_port_in_use 8001; then
        echo "Port 8001 is already in use."
        
        # Check if it's our API server
        if pgrep -f "python simple_api.py" >/dev/null; then
            echo "Simple API server is already running."
            
            # Check if it's responding
            if curl -s http://localhost:8001/ >/dev/null 2>&1; then
                echo "Simple API server is responding correctly."
                SIMPLE_API_PID=$(pgrep -f "python simple_api.py")
                echo "Using existing Simple API server (PID: $SIMPLE_API_PID)"
                return 0
            else
                echo "Simple API server is not responding. Restarting..."
                pkill -f "python simple_api.py" || true
                sleep 1
            fi
        else
            echo "Another process is using port 8001. Stopping it..."
            if command -v lsof >/dev/null 2>&1; then
                lsof -i:8001 -t | xargs kill 2>/dev/null || true
            else
                echo "Warning: Cannot automatically stop the process using port 8001."
                echo "Please stop it manually and try again."
                return 1
            fi
            sleep 1
        fi
    fi
    
    # Start the API server
    if [ -d "venv" ]; then
        echo "Using virtual environment..."
        source venv/bin/activate
        python simple_api.py > simple_api_logs.txt 2>&1 &
        deactivate
    else
        python simple_api.py > simple_api_logs.txt 2>&1 &
    fi
    SIMPLE_API_PID=$!
    
    # Wait for the API to start
    echo "Waiting for simple API to start..."
    for i in {1..10}; do
        sleep 1
        if curl -s http://localhost:8001/ >/dev/null 2>&1; then
            echo "Simple API server started successfully (PID: $SIMPLE_API_PID)"
            return 0
        fi
        echo -n "."
    done
    
    echo "Error: Simple API failed to start. Check simple_api_logs.txt for details."
    echo "Last few lines of the log:"
    tail -n 10 simple_api_logs.txt
    return 1
}

# Function to run the complex API
run_complex_api() {
    echo "Starting complex API server on port 8000..."
    
    # Check if the port is already in use
    if check_port_in_use 8000; then
        echo "Port 8000 is already in use."
        
        # Check if it's our API server
        if pgrep -f "python main.py" >/dev/null; then
            echo "Complex API server is already running."
            
            # Check if it's responding
            if curl -s http://localhost:8000/ >/dev/null 2>&1; then
                echo "Complex API server is responding correctly."
                COMPLEX_API_PID=$(pgrep -f "python main.py")
                echo "Using existing Complex API server (PID: $COMPLEX_API_PID)"
                return 0
            else
                echo "Complex API server is not responding. Restarting..."
                pkill -f "python main.py" || true
                sleep 1
            fi
        else
            echo "Another process is using port 8000. Stopping it..."
            if command -v lsof >/dev/null 2>&1; then
                lsof -i:8000 -t | xargs kill 2>/dev/null || true
            else
                echo "Warning: Cannot automatically stop the process using port 8000."
                echo "Please stop it manually and try again."
                return 1
            fi
            sleep 1
        fi
    fi
    
    # Start the API server
    if [ -d "venv" ]; then
        echo "Using virtual environment..."
        source venv/bin/activate
        python main.py --component api --api-host 0.0.0.0 --api-port 8000 > complex_api_logs.txt 2>&1 &
        deactivate
    else
        python main.py --component api --api-host 0.0.0.0 --api-port 8000 > complex_api_logs.txt 2>&1 &
    fi
    COMPLEX_API_PID=$!
    
    # Wait for the API to start
    echo "Waiting for complex API to start..."
    for i in {1..15}; do
        sleep 1
        if curl -s http://localhost:8000/ >/dev/null 2>&1; then
            echo "Complex API server started successfully (PID: $COMPLEX_API_PID)"
            return 0
        fi
        echo -n "."
    done
    
    echo "Error: Complex API failed to start. Check complex_api_logs.txt for details."
    echo "Last few lines of the log:"
    tail -n 10 complex_api_logs.txt
    return 1
}

# Function to run the dashboard
run_dashboard() {
    echo "Starting dashboard server on port 8080..."
    
    # Check if the port is already in use
    if check_port_in_use 8080; then
        echo "Port 8080 is already in use."
        
        # Check if it's our dashboard server
        if pgrep -f "python serve_dashboard.py" >/dev/null; then
            echo "Dashboard server is already running."
            
            # Check if it's responding
            if curl -s -I http://localhost:8080/simple_dashboard.html 2>&1 | grep -q "200 OK"; then
                echo "Dashboard server is responding correctly."
                DASHBOARD_PID=$(pgrep -f "python serve_dashboard.py")
                echo "Using existing Dashboard server (PID: $DASHBOARD_PID)"
                echo "Dashboard is available at: http://localhost:8080/simple_dashboard.html"
                return 0
            else
                echo "Dashboard server is not responding. Restarting..."
                pkill -f "python serve_dashboard.py" || true
                sleep 1
            fi
        else
            echo "Another process is using port 8080. Stopping it..."
            if command -v lsof >/dev/null 2>&1; then
                lsof -i:8080 -t | xargs kill 2>/dev/null || true
            else
                echo "Warning: Cannot automatically stop the process using port 8080."
                echo "Please stop it manually and try again."
                return 1
            fi
            sleep 1
        fi
    fi
    
    # Start the dashboard server
    if [ -d "venv" ]; then
        echo "Using virtual environment..."
        source venv/bin/activate
        python serve_dashboard.py > dashboard_logs.txt 2>&1 &
        deactivate
    else
        python serve_dashboard.py > dashboard_logs.txt 2>&1 &
    fi
    DASHBOARD_PID=$!
    
    # Wait for the dashboard server to start
    echo "Waiting for dashboard server to start..."
    for i in {1..10}; do
        sleep 1
        if curl -s -I http://localhost:8080/simple_dashboard.html 2>&1 | grep -q "200 OK"; then
            echo "Dashboard server started successfully (PID: $DASHBOARD_PID)"
            echo "Dashboard is available at: http://localhost:8080/simple_dashboard.html"
            return 0
        fi
        echo -n "."
    done
    
    echo "Error: Dashboard server failed to start. Check dashboard_logs.txt for details."
    echo "Last few lines of the log:"
    tail -n 10 dashboard_logs.txt
    return 1
}

# Check dependencies first
check_dependencies

# Store PIDs for cleanup message
PIDS=()

# Parse command line arguments
if [ $# -eq 0 ]; then
    # Default: run everything
    run_simple_api && PIDS+=($SIMPLE_API_PID)
    run_dashboard && PIDS+=($DASHBOARD_PID)
else
    case "$1" in
        --help)
            show_usage
            exit 0
            ;;
        --stop)
            stop_all_servers
            exit 0
            ;;
        --simple-api)
            run_simple_api && PIDS+=($SIMPLE_API_PID)
            ;;
        --complex-api)
            run_complex_api && PIDS+=($COMPLEX_API_PID)
            ;;
        --both-apis)
            run_simple_api && PIDS+=($SIMPLE_API_PID)
            run_complex_api && PIDS+=($COMPLEX_API_PID)
            ;;
        --dashboard)
            run_dashboard && PIDS+=($DASHBOARD_PID)
            ;;
        --all)
            run_simple_api && PIDS+=($SIMPLE_API_PID)
            run_complex_api && PIDS+=($COMPLEX_API_PID)
            run_dashboard && PIDS+=($DASHBOARD_PID)
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
    echo "Done! To stop the servers, run: ./run_dashboard.sh --stop"
    echo "Or manually with: kill ${PIDS[@]}"
fi

# Print final instructions
echo ""
echo "To access the dashboard, open this URL in your browser:"
echo "http://localhost:8080/simple_dashboard.html"
echo ""
echo "If you encounter any issues:"
echo "1. Check the log files: simple_api_logs.txt and dashboard_logs.txt"
echo "2. Make sure all required Python packages are installed: pip install -r requirements.txt"
echo "3. Try stopping all servers and starting again: ./run_dashboard.sh --stop && ./run_dashboard.sh" 