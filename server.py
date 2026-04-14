import http.server
import socketserver
import os
import socket

PORT = 8080
DIRECTORY = "/Users/nikee/Desktop/ResQNow/"

class SmartHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Force no-cache so your changes show up instantly
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def guess_type(self, path):
        # Force correct mimetypes to fix white-screen issues on macOS
        if path.endswith(".html"):
            return "text/html"
        if path.endswith(".js"):
            return "application/javascript"
        if path.endswith(".css"):
            return "text/css"
        return super().guess_type(path)

# Auto-clear port if busy
try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(('localhost', PORT)) == 0:
            print(f"Port {PORT} in use. Resetting...")
            os.system(f"lsof -ti:{PORT} | xargs kill -9 2>/dev/null")
except:
    pass

with socketserver.TCPServer(("", PORT), SmartHandler) as httpd:
    print(f"-------------------------------------------")
    print(f"🚀 Mission Control Live: http://localhost:{PORT}")
    print(f"-------------------------------------------")
    httpd.serve_forever()
