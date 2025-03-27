#!/bin/bash
set -e

# Trap SIGTERM and SIGINT
trap "echo Received signal to terminate; kill -TERM \$API_PID \$WEB_PID 2>/dev/null; exit" SIGTERM SIGINT

echo "Starting SEC Finance API..."
# Export environment variables for the API
export API_HOST=0.0.0.0
export API_PORT=8002

# Set SEC API User-Agent environment variables with defaults
export SEC_API_COMPANY_NAME=${SEC_API_COMPANY_NAME:-"Finance Project"}
export SEC_API_CONTACT_EMAIL=${SEC_API_CONTACT_EMAIL:-"user@example.com"}
export SEC_API_PHONE_NUMBER=${SEC_API_PHONE_NUMBER:-"555-555-5555"}

echo "Using SEC API User-Agent: ${SEC_API_COMPANY_NAME} ${SEC_API_CONTACT_EMAIL} ${SEC_API_PHONE_NUMBER}"

# Start the API
python -m simple_api --log-level=INFO &
API_PID=$!

# Wait for API to be available with retry logic
echo "Waiting for API to be available..."
MAX_RETRIES=60  # Increase max retries
RETRY_COUNT=0
API_READY=false

# Sleep a moment to let the API start
sleep 5

while [ $RETRY_COUNT -lt $MAX_RETRIES ] && [ "$API_READY" = false ]; do
  if curl -s http://localhost:8002/health > /dev/null; then
    API_READY=true
    echo "API is ready!"
  else
    RETRY_COUNT=$((RETRY_COUNT+1))
    echo "API not ready yet (attempt ${RETRY_COUNT}/${MAX_RETRIES})..."
    
    # Check if API process is still running
    if ! ps -p $API_PID > /dev/null; then
      echo "Error: API process has died unexpectedly"
      echo "API logs:"
      cat /app/simple_api_logs.txt 2>/dev/null || echo "No logs found"
      exit 1
    fi
    
    sleep 2  # Longer sleep between retries
  fi
done

if [ "$API_READY" = false ]; then
  echo "Error: API failed to start after ${MAX_RETRIES} attempts"
  echo "API logs:"
  cat /app/simple_api_logs.txt 2>/dev/null || echo "No logs found"
  exit 1
fi

# Export API_URL environment variables to be used by the web server
# INTERNAL_API_URL is for the container's internal communication
INTERNAL_API_URL=${INTERNAL_API_URL:-"http://localhost:8002"}
# EXTERNAL_API_URL is what the browser will use (through port mapping)
EXTERNAL_API_URL=${EXTERNAL_API_URL:-"http://localhost:8002"}

echo "Using INTERNAL_API_URL: ${INTERNAL_API_URL} for container communication"
echo "Using EXTERNAL_API_URL: ${EXTERNAL_API_URL} for browser access"

# Create a simple script to inject API_URL into HTML files when serving
cat > /app/inject_api_url.py << EOF
import os
import sys
import http.server
import socketserver

# Use the EXTERNAL_API_URL for browser access
API_URL = os.environ.get("EXTERNAL_API_URL", "http://localhost:8002")
PORT = int(os.environ.get("PORT", 8080))

class APIURLHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        http.server.SimpleHTTPRequestHandler.end_headers(self)

    def do_GET(self):
        if self.path.endswith(".html"):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            # Read the HTML file
            with open("." + self.path, "r") as f:
                content = f.read()
            
            # Replace API URL placeholders with actual API_URL for browser access
            content = content.replace('const API_URL = "http://localhost:8002";', f'const API_URL = "{API_URL}";')
            content = content.replace('"http://localhost:8002/', f'"{API_URL}/')
            content = content.replace("'http://localhost:8002/", f"'{API_URL}/")
            
            self.wfile.write(content.encode())
            return
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

print(f"Starting web server on port {PORT}, using API_URL: {API_URL}")
with socketserver.TCPServer(("", PORT), APIURLHandler) as httpd:
    httpd.serve_forever()
EOF

echo "Starting web server..."
python /app/inject_api_url.py &
WEB_PID=$!

echo "Finance dashboard is now available at http://localhost:8080/simple_dashboard.html"
echo "Using API at ${EXTERNAL_API_URL} for browser access"

# Wait for either process to exit
wait -n $API_PID $WEB_PID

# Get exit status
EXIT_STATUS=$?

echo "A process has exited with status ${EXIT_STATUS}"

# Kill the other process
kill -TERM $API_PID $WEB_PID 2>/dev/null || true

# Exit with the same status
exit $EXIT_STATUS 