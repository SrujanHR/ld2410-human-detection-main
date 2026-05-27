"""
web_server.py
Serves output.json and a live HTML dashboard on a local HTTP port.
No external libraries needed — uses Python's built-in http.server.
"""

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>LD2410S Human Detection Dashboard</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', monospace; background: #0d1117; color: #c9d1d9; }
    h1 { text-align: center; padding: 20px; color: #58a6ff; letter-spacing: 2px; }
    #direction { text-align: center; font-size: 2em; margin: 10px 0;
                 padding: 10px; background: #161b22; border-radius: 8px; }
    #cards { display: flex; justify-content: center; gap: 20px;
             flex-wrap: wrap; padding: 20px; }
    .card { background: #161b22; border-radius: 12px; padding: 20px;
            width: 200px; border: 1px solid #30363d; text-align: center; }
    .card h2 { font-size: 1em; color: #8b949e; margin-bottom: 10px; }
    .card .status { font-size: 1.5em; margin: 8px 0; }
    .card .dist { font-size: 2em; font-weight: bold; color: #58a6ff; }
    .card .energy { font-size: 0.85em; color: #8b949e; margin-top: 6px; }
    .present { color: #3fb950; }
    .absent  { color: #f85149; }
    #timestamp { text-align: center; font-size: 0.8em;
                 color: #484f58; padding-bottom: 20px; }
  </style>
</head>
<body>
  <h1>🔍 LD2410S Human Detection System</h1>
  <div id="direction">Direction: —</div>
  <div id="cards"></div>
  <div id="timestamp"></div>

  <script>
    const SENSOR_NAMES = ["Sensor_1", "Sensor_2", "Sensor_3"];
    const POSITIONS    = ["LEFT", "CENTER", "RIGHT"];

    function fetchData() {
      fetch('/output.json')
        .then(r => r.json())
        .then(data => {
          document.getElementById('direction').textContent =
            'Direction: ' + (data.direction || 'No Detection');
          document.getElementById('timestamp').textContent =
            'Last update: ' + (data.timestamp || '');

          const cards = document.getElementById('cards');
          cards.innerHTML = '';
          SENSOR_NAMES.forEach((name, i) => {
            const s = data[name];
            if (!s) return;
            const div = document.createElement('div');
            div.className = 'card';
            div.innerHTML = `
              <h2>${name} (${POSITIONS[i]})</h2>
              <div class="status ${s.presence ? 'present' : 'absent'}">
                ${s.presence ? '✔ DETECTED' : '✗ Clear'}
              </div>
              <div class="dist">${s.distance_cm} cm</div>
              <div class="energy">
                Move: ${s.moving_energy} &nbsp;|&nbsp; Static: ${s.static_energy}
              </div>`;
            cards.appendChild(div);
          });
        })
        .catch(() => {});
    }

    setInterval(fetchData, 500);
    fetchData();
  </script>
</body>
</html>"""


class _Handler(BaseHTTPRequestHandler):
    """Minimal HTTP handler: serves dashboard and output.json."""

    output_file: str = "output.json"  # set by start_web_server()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html", DASHBOARD_HTML.encode())
        elif self.path == "/output.json":
            try:
                with open(self.output_file, "rb") as f:
                    self._send(200, "application/json", f.read())
            except FileNotFoundError:
                self._send(200, "application/json", b"{}")
        else:
            self._send(404, "text/plain", b"Not Found")

    def _send(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # suppress default access logs


def start_web_server(output_file: str, port: int = 8000):
    """
    Start a blocking HTTP server.
    Call in a daemon thread so it doesn't prevent program exit.
    """
    _Handler.output_file = output_file
    server = HTTPServer(("0.0.0.0", port), _Handler)
    print(f"[WebServer] Listening on port {port}")
    server.serve_forever()
