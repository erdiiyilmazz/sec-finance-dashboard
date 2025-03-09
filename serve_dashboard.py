#!/usr/bin/env python3
import http.server
import socketserver
import os
import webbrowser
import threading
import time

# Configuration
PORT = 8080
DASHBOARD_FILE = "simple_dashboard.html"

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect root to the dashboard
        if self.path == '/':
            self.path = f'/{DASHBOARD_FILE}'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def open_browser():
    """Open the browser after a short delay to ensure the server is running."""
    time.sleep(1)
    url = f"http://localhost:{PORT}/{DASHBOARD_FILE}"
    print(f"Opening dashboard at: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    # Change to the directory containing this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Start the browser in a separate thread
    threading.Thread(target=open_browser).start()
    
    # Start the HTTP server
    with socketserver.TCPServer(("", PORT), MyHttpRequestHandler) as httpd:
        print(f"Serving dashboard at http://localhost:{PORT}/{DASHBOARD_FILE}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.") 