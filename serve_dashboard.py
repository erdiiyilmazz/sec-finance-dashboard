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
            
            # Check if this is a relative URL (doesn't start with http)
            if not sec_url_path.startswith('http'):
                # This is a relative URL, we need to resolve it against the base URL
                # First, check if we have a referer header
                referer = self.headers.get('Referer', '')
                if referer and '/sec-proxy/' in referer:
                    # Extract the base URL from the referer
                    referer_parts = referer.split('/sec-proxy/')
                    if len(referer_parts) > 1:
                        base_url_encoded = referer_parts[1]
                        base_url = urllib.parse.unquote(base_url_encoded)
                        
                        # Extract the directory part of the base URL
                        base_dir = '/'.join(base_url.split('/')[:-1]) + '/'
                        
                        # Resolve the relative URL against the base directory
                        sec_url = base_dir + sec_url_path
                        print(f"Resolved relative URL: {sec_url_path} -> {sec_url}")
                    else:
                        self.send_error(500, f"SEC Proxy Error: unable to resolve relative URL from referer")
                        return
                else:
                    self.send_error(500, f"SEC Proxy Error: unknown url type: '{sec_url_path}'")
                    return
            else:
                # This is an absolute URL
                sec_url = urllib.parse.unquote(sec_url_path)
            
            print(f"Proxying request to SEC: {sec_url}")
            
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