#!/usr/bin/env python3
"""
Simple CORS proxy server for NASA API calls.
Run: python server.py
Then access http://localhost:8000
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urljoin, urlparse, parse_qs
import urllib.request
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProxyHandler(SimpleHTTPRequestHandler):
    """Handle both static files and API proxying"""
    
    API_BASE = '/api/'
    
    def do_GET(self):
        """Handle GET requests - route API calls to proxy, others to static files"""
        if self.path.startswith(self.API_BASE):
            self.handle_api_request()
        else:
            super().do_GET()
    
    def handle_api_request(self):
        """Proxy API requests and add CORS headers"""
        # Parse the proxied URL from query parameter
        # Format: /api/?url=https://example.com/endpoint
        query = parse_qs(urlparse(self.path).query)
        if 'url' not in query:
            self.send_error(400, 'Missing url parameter')
            return
        
        target_url = query['url'][0]
        logger.info(f"Proxying: {target_url}")
        
        try:
            # Fetch from target API
            with urllib.request.urlopen(target_url, timeout=10) as response:
                data = response.read()
                content_type = response.headers.get('Content-Type', 'application/json')
            
            # Send response with CORS headers
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Content-Length', len(data))
            self.end_headers()
            self.wfile.write(data)
            
        except urllib.error.HTTPError as e:
            logger.error(f"HTTP Error {e.code}: {target_url}")
            self.send_error(e.code, str(e))
        except urllib.error.URLError as e:
            logger.error(f"URL Error: {e.reason}")
            self.send_error(503, f"Service unavailable: {e.reason}")
        except Exception as e:
            logger.error(f"Error proxying {target_url}: {e}")
            self.send_error(500, str(e))
    
    def end_headers(self):
        """Add CORS headers to all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS, HEAD')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging, use our logger"""
        logger.info(format % args)

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, ProxyHandler)
    logger.info('Server running at http://localhost:8000')
    logger.info('Serving from: ' + __file__.rsplit('/', 1)[0])
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        httpd.shutdown()
