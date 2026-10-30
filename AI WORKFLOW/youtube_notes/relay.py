"""Transcript relay — run this on your home PC.

YouTube blocks Streamlit Cloud's IPs, but not your home (residential) IP.
The cloud app asks this relay for transcripts; the relay fetches them from YouTube.

    Streamlit Cloud app → Cloudflare Tunnel → this relay (your PC) → YouTube

Run:
    python "AI WORKFLOW/youtube_notes/relay.py"
    cloudflared tunnel --url http://localhost:8000      (in a second terminal)

Needs RELAY_TOKEN in .env (any long random string) — the cloud app must send
the same token, so strangers who find the tunnel URL can't use your IP.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
from youtube_transcript_api import NoTranscriptFound, YouTubeTranscriptApi

for folder in Path(__file__).resolve().parents:
    if (folder / ".env").exists():
        load_dotenv(folder / ".env")
        break

TOKEN = os.getenv("RELAY_TOKEN")
PORT = int(os.getenv("RELAY_PORT", "8000"))


def fetch(video_id: str):
    """Same logic as the app: prefer English, else the first available language."""
    api = YouTubeTranscriptApi()
    try:
        transcript = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
    except NoTranscriptFound:
        transcript = next(iter(api.list(video_id))).fetch()
    return {
        "snippets": [{"start": s.start, "text": s.text} for s in transcript.snippets],
        "language_code": transcript.language_code,
    }


class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path != "/transcript":
            return self.send_json(404, {"error": "not found"})
        if self.headers.get("X-Relay-Token") != TOKEN:
            return self.send_json(401, {"error": "bad token"})
        video_id = parse_qs(url.query).get("video_id", [""])[0]
        if not video_id:
            return self.send_json(400, {"error": "video_id missing"})
        try:
            self.send_json(200, fetch(video_id))
        except Exception as e:
            self.send_json(502, {"error": f"{type(e).__name__}: {e}"})


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set RELAY_TOKEN in .env first.")
    print(f"Relay running on http://localhost:{PORT}  (Ctrl+C to stop)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
