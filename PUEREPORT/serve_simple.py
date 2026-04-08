
import http.server
import socketserver
import webbrowser
import sys

def find_free_port(start_port):
    import socket
    port = start_port
    while port < start_port + 100:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            port += 1
    return start_port

PORT = find_free_port(5500)
Handler = http.server.SimpleHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/index.html"
        print(f"Serving Simple Frontend at {url}")
        webbrowser.open(url)
        httpd.serve_forever()
except Exception as e:
    print(f"Failed to start server: {e}")
