#!/usr/bin/env python3
import http.server
import socketserver
import socket
import struct
import threading
import time

INGEST_HOST = "127.0.0.1"
INGEST_PORT = 8765
HTTP_HOST = "0.0.0.0"
HTTP_PORT = 8080

latest = None
lock = threading.Lock()
clients = 0

HTML = """<!doctype html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Termux Screen Stream</title>
<style>
html,body{margin:0;background:#111;color:#eee;font-family:system-ui}
header{padding:12px 16px;background:#1b1b1b;position:sticky;top:0}
img{display:block;max-width:100%;height:auto;margin:auto}
small{opacity:.7}
</style>
</head>
<body>
<header>
<b>Termux Screen Stream</b><br>
<small>Live MJPEG stream</small>
</header>
<img src="/mjpeg" alt="Screen stream">
</body>
</html>
"""

def ingest_client(conn, addr):
    global latest, clients
    clients += 1
    try:
        with conn:
            while True:
                hdr = conn.recv(4)
                if not hdr:
                    break
                while len(hdr) < 4:
                    part = conn.recv(4-len(hdr))
                    if not part:
                        return
                    hdr += part
                n = struct.unpack(">I", hdr)[0]
                if n <= 0 or n > 20_000_000:
                    break
                data = bytearray()
                while len(data) < n:
                    part = conn.recv(min(65536, n-len(data)))
                    if not part:
                        return
                    data.extend(part)
                with lock:
                    latest = bytes(data)
    except (ConnectionError, OSError):
        pass
    finally:
        clients -= 1

def ingest_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((INGEST_HOST, INGEST_PORT))
        s.listen(2)
        print(f"[+] APK ingest: {INGEST_HOST}:{INGEST_PORT}")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=ingest_client, args=(conn, addr), daemon=True).start()

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("[HTTP]", fmt % args)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/mjpeg":
            self.send_response(200)
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            last = None
            try:
                while True:
                    with lock:
                        frame = latest
                    if frame is not None and frame != last:
                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                        self.wfile.write(frame)
                        self.wfile.write(b"\r\n")
                        self.wfile.flush()
                        last = frame
                    else:
                        time.sleep(0.03)
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            return

        self.send_error(404)

def main():
    threading.Thread(target=ingest_server, daemon=True).start()
    with socketserver.ThreadingTCPServer((HTTP_HOST, HTTP_PORT), Handler) as httpd:
        httpd.allow_reuse_address = True
        print(f"[+] Browser: http://127.0.0.1:{HTTP_PORT}")
        print(f"[+] LAN/public binding: {HTTP_HOST}:{HTTP_PORT}")
        print("[+] Waiting for APK frames...")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
