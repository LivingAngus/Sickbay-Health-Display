"""
Shared Oura API client: token refresh + authenticated GET requests.

Other scripts (oura_fetch.py, the future relay prototype, etc.) should
import from here rather than duplicating token-handling logic. This is the
one place that knows about oura_credentials.json / oura_tokens.json.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDS_PATH = os.path.join(SCRIPT_DIR, "oura_credentials.json")
TOKENS_PATH = os.path.join(SCRIPT_DIR, "oura_tokens.json")

TOKEN_URL = "https://api.ouraring.com/oauth/token"
API_BASE = "https://api.ouraring.com/v2/usercollection"


def _load_json(path):
    with open(path) as f:
        return json.load(f)


def _save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_credentials():
    return _load_json(CREDS_PATH)


def load_tokens():
    return _load_json(TOKENS_PATH)


def save_tokens(tokens):
    _save_json(TOKENS_PATH, tokens)


def refresh_access_token():
    """
    Exchange the current refresh_token for a new access_token. Oura rotates
    the refresh_token on every use too — the old one stops working the
    moment a new one is issued — so the new pair is saved back to
    oura_tokens.json immediately. Returns the fresh tokens dict.
    """
    creds = load_credentials()
    tokens = load_tokens()

    data = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
    }).encode()

    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req) as resp:
            new_tokens = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Token refresh failed: HTTP {e.code}")
        print(e.read().decode())
        raise

    save_tokens(new_tokens)
    print(f"Refreshed access token — expires in {new_tokens.get('expires_in')} seconds.")
    return new_tokens


def get(path, params=None, _retried=False):
    """
    Authenticated GET against the Oura API, e.g. get("daily_readiness",
    {"start_date": "2026-09-01", "end_date": "2026-09-18"}).

    Automatically refreshes and retries once on a 401 (expired/rejected
    access token), so callers never need to think about token lifetime.
    Returns the parsed JSON response, or None on a non-recoverable error.
    """
    tokens = load_tokens()
    url = f"{API_BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {tokens['access_token']}")

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 401 and not _retried:
            print("Access token expired/rejected — refreshing and retrying once...")
            refresh_access_token()
            return get(path, params, _retried=True)
        print(f"HTTP {e.code} calling {path}")
        print(e.read().decode())
        return None
