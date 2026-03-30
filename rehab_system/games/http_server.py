"""
HYPERION REHAB - No-Cache HTTP Server
Forces Cache-Control: no-cache so the browser ALWAYS loads the latest index.html.
Serves from the current working directory (set by the launcher).
"""
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

class NoCacheHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        pass  # Suppress noisy access logs

if __name__ == "__main__":
    PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    httpd = HTTPServer(("", PORT), NoCacheHandler)
    print(f"[HTTP] Serving at http://localhost:{PORT} (no-cache)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("[HTTP] Shutdown")

