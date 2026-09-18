"""
One-time OAuth2 authorization + token exchange for the Oura API.

Reads client_id/client_secret from oura_credentials.json (gitignored, sits
next to this script), opens your browser to Oura's consent screen, catches
the redirect on a temporary local server, and immediately exchanges the
authorization code for an access token + refresh token (Oura's codes expire
in ~30 seconds, so this has to happen automatically, not by hand).

Saves the result to oura_tokens.json (also gitignored). Re-run this any
time you need a fresh refresh token (e.g. if it's ever revoked) — for
day-to-day use, a separate script should use the saved refresh_token to
mint new access tokens without repeating the browser step.
"""

import http.server
import json
import os
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(SCRIPT_DIR, "oura_credentials.json")
TOKENS_PATH = os.path.join(SCRIPT_DIR, "oura_tokens.json")

REDIRECT_URI = "http://localhost:3000/callback"
AUTHORIZE_URL = "https://cloud.ouraring.com/oauth/authorize"
TOKEN_URL = "https://api.ouraring.com/oauth/token"
SCOPES = "personal daily heartrate spo2"

with open(CREDS_PATH) as f:
    creds = json.load(f)
CLIENT_ID = creds["client_id"]
CLIENT_SECRET = creds["client_secret"]

STATE = secrets.token_urlsafe(16)
result = {}


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        qs = urllib.parse.parse_qs(parsed.query)
        code = qs.get("code", [None])[0]
        got_state = qs.get("state", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()

        if not code or got_state != STATE:
            self.wfile.write(b"<h1>Something went wrong. Check the terminal.</h1>")
            result["error"] = f"missing code or state mismatch (got state={got_state!r})"
        else:
            self.wfile.write(b"<h1>Success! You can close this tab.</h1>")
            result["code"] = code

        threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args):
        pass  # keep the terminal quiet


def main():
    server = http.server.HTTPServer(("localhost", 3000), CallbackHandler)

    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": STATE,
    }
    auth_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(params)
    print(f"Opening browser to authorize:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server.serve_forever()

    if "error" in result:
        print("ERROR:", result["error"])
        sys.exit(1)

    code = result["code"]
    print("Got authorization code, exchanging for tokens...")

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Token exchange failed: HTTP {e.code}")
        print(e.read().decode())
        sys.exit(1)

    with open(TOKENS_PATH, "w") as f:
        json.dump(tokens, f, indent=2)

    print(f"Success. Tokens saved to {TOKENS_PATH}")
    print(f"Access token expires in {tokens.get('expires_in')} seconds.")
    print("Refresh token saved — that's what future scripts should use to mint new access tokens.")


if __name__ == "__main__":
    main()
