#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
import threading
import signal
import sys
import urllib.request
import urllib.parse
import re
import datetime

# Configuration
PORT = 8080
DASHBOARD_FILE = "simple_dashboard.html"

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the dashboard."""
    
    def do_GET(self):
        """Handle GET requests."""
        # Redirect root to the dashboard
        if self.path == '/':
            self.send_response(302)
            self.send_header('Location', '/simple_dashboard.html')
            self.end_headers()
            return
            
        # Handle SEC filing proxy requests
        if self.path.startswith('/sec-proxy/'):
            self.handle_sec_proxy()
            return
            
        # Default behavior for other requests
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def handle_sec_proxy(self):
        """Handle proxy requests to SEC website."""
        try:
            # Extract the SEC URL from the path
            sec_url_path = self.path[len('/sec-proxy/'):]
            
            # Decode the URL first
            sec_url = urllib.parse.unquote(sec_url_path)
            
            print(f"Proxying request to SEC: {sec_url}")
            
            # Check for future filing dates in the URL
            # Typical format: /Archives/edgar/data/0000320193/000032019324000123/aapl-20240928.htm
            
            # Extract filing date if present in URL
            date_pattern = r'/[a-zA-Z]+-(\d{8})\.htm'
            date_match = re.search(date_pattern, sec_url)
            
            if date_match:
                filing_date_str = date_match.group(1)
                try:
                    # Format is YYYYMMDD
                    filing_year = int(filing_date_str[0:4])
                    filing_month = int(filing_date_str[4:6])
                    filing_day = int(filing_date_str[6:8])
                    
                    filing_date = datetime.date(filing_year, filing_month, filing_day)
                    current_date = datetime.date.today()
                    
                    print(f"Comparing dates - Filing date: {filing_date} | Current date: {current_date}")
                    
                    # Don't use > operator for dates as it might lead to incorrect comparisons
                    # Instead, check each component explicitly to ensure correct date comparison
                    is_future_date = False
                    
                    if filing_year > current_date.year:
                        is_future_date = True
                    elif filing_year == current_date.year:
                        if filing_month > current_date.month:
                            is_future_date = True
                        elif filing_month == current_date.month:
                            if filing_day > current_date.day:
                                is_future_date = True
                    
                    if is_future_date:
                        print(f"Request for future filing date detected: {filing_date_str}")
                        future_date_html = f"""
                        <html>
                        <head>
                            <title>Future Filing Date</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                                h1 {{ color: #333; }}
                                .error {{ color: #d9534f; }}
                                .info {{ color: #5bc0de; }}
                            </style>
                        </head>
                        <body>
                            <div class="container">
                                <h1>Future Filing Date</h1>
                                <p class="error">Error: The requested SEC filing has a future date and is not yet available.</p>
                                <p>The filing date in the URL ({filing_date.strftime('%Y-%m-%d')}) is in the future. SEC filings are not available until their filing date has passed.</p>
                                <p class="info">Current date: {current_date.strftime('%Y-%m-%d')}</p>
                                <p class="info">Requested URL: {sec_url}</p>
                                <p>Please try a different filing with a past date.</p>
                            </div>
                        </body>
                        </html>
                        """
                        self.send_response(404)
                        self.send_header('Content-Type', 'text/html')
                        self.send_header('Content-Length', str(len(future_date_html.encode('utf-8'))))
                        self.end_headers()
                        self.wfile.write(future_date_html.encode('utf-8'))
                        return
                except (ValueError, IndexError) as e:
                    print(f"Error parsing date from URL: {e}")
                    # Continue with request if date parsing fails
            
            # Set up headers to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': 'https://www.sec.gov/'
            }
            
            try:
                # Create a request with headers
                req = urllib.request.Request(sec_url, headers=headers)
                
                # Make the request to SEC
                with urllib.request.urlopen(req) as response:
                    # Get the content type
                    content_type = response.getheader('Content-Type', 'text/html')
                    
                    # Read the response data
                    data = response.read()
                    
                    # If this is HTML content, we need to rewrite URLs to use our proxy
                    if 'text/html' in content_type.lower():
                        try:
                            # Decode the HTML
                            html_content = data.decode('utf-8')
                            
                            # Replace relative URLs with proxied URLs
                            # Handle src attributes (images, scripts, etc.)
                            html_content = html_content.replace(' src="/', ' src="/sec-proxy/https://www.sec.gov/')
                            html_content = html_content.replace(" src='", " src='/sec-proxy/")
                            
                            # Handle href attributes (links, stylesheets, etc.)
                            html_content = html_content.replace(' href="/', ' href="/sec-proxy/https://www.sec.gov/')
                            html_content = html_content.replace(" href='", " href='/sec-proxy/")
                            
                            # Re-encode the HTML
                            data = html_content.encode('utf-8')
                        except UnicodeDecodeError:
                            # If we can't decode the HTML, just pass it through unchanged
                            print("Warning: Could not decode HTML content for URL rewriting")
                    
                    # Send the response to the client
                    self.send_response(200)
                    self.send_header('Content-Type', content_type)
                    self.send_header('Content-Length', str(len(data)))
                    # Allow embedding in iframe
                    self.send_header('X-Frame-Options', 'ALLOWALL')
                    self.send_header('Content-Security-Policy', "frame-ancestors 'self' *")
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(data)
                    
                    print(f"Successfully proxied SEC request: {sec_url}")
                    
            except urllib.error.HTTPError as e:
                print(f"HTTP Error proxying SEC request: {e.code} - {e.reason} for URL: {sec_url}")
                if e.code == 404:
                    # Create a user-friendly HTML response with a link to view directly on SEC website
                    error_html = f"""
                    <html>
                    <head>
                        <title>SEC Filing Not Found</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                            .container {{ max-width: 800px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                            h1 {{ color: #333; }}
                            .error {{ color: #d9534f; }}
                            .info {{ color: #5bc0de; }}
                            .action {{ margin-top: 20px; }}
                            a.button {{ background-color: #0275d8; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; }}
                            a.button:hover {{ background-color: #025aa5; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>SEC Filing Not Available</h1>
                            <p class="error">Error: The requested SEC filing could not be found (HTTP 404)</p>
                            <p>The SEC server returned a 404 (Not Found) error for this filing. This could be because:</p>
                            <ul>
                                <li>The filing has been moved or removed from the SEC website</li>
                                <li>The filing is not yet publicly available (future filing date)</li>
                                <li>The URL format has changed on the SEC website</li>
                            </ul>
                            <p class="info">Requested URL: {sec_url}</p>
                            <div class="action">
                                <p>You can try to view this filing directly on the SEC website:</p>
                                <a href="{sec_url}" target="_blank" class="button">View on SEC.gov</a>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    self.send_response(404)
                    self.send_header('Content-Type', 'text/html')
                    self.send_header('Content-Length', str(len(error_html.encode('utf-8'))))
                    self.end_headers()
                    self.wfile.write(error_html.encode('utf-8'))
                else:
                    self.send_error(e.code, f"SEC Proxy Error: {e.reason}")
            except urllib.error.URLError as e:
                print(f"URL Error proxying SEC request: {e.reason} for URL: {sec_url}")
                self.send_error(500, f"SEC Proxy Error: {e.reason}")
                
        except Exception as e:
            print(f"General error in SEC proxy: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_error(500, f"SEC Proxy Error: {str(e)}")
    
    def do_POST(self):
        """Handle POST requests."""
        # Return 501 Not Implemented for Akamai pixel requests
        if '/akam/' in self.path:
            self.send_response(501)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"POST requests not supported")
            return
            
        # Default behavior for other requests
        return http.server.SimpleHTTPRequestHandler.do_POST(self)

def open_browser():
    """Open the browser to the dashboard."""
    url = f"http://localhost:{PORT}/simple_dashboard.html"
    print(f"Opening dashboard at {url}")
    webbrowser.open(url)

def signal_handler(sig, frame):
    """Handle Ctrl+C to gracefully shut down the server."""
    print("\nShutting down server...")
    sys.exit(0)

def run_server():
    """Run the HTTP server."""
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Create and start the server
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Serving dashboard at http://localhost:{PORT}")
        print("Press Ctrl+C to stop the server")
        
        # Open browser after a short delay
        threading.Timer(1.0, open_browser).start()
        
        # Start the server
        httpd.serve_forever()

if __name__ == "__main__":
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    run_server() 