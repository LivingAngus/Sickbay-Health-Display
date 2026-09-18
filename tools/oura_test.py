"""
Sanity check: use the saved access token to pull one real reading from the
Oura API. Confirms the whole OAuth chain actually works end-to-end before
any ESP32 firmware gets written.
"""

import datetime
import json
import os
import urllib.error
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKENS_PATH = os.path.join(SCRIPT_DIR, "oura_tokens.json")

API_BASE = "https://api.ouraring.com/v2/usercollection"

with open(TOKENS_PATH) as f:
    tokens = json.load(f)

ACCESS_TOKEN = tokens["access_token"]


def get(path, params=None):
    url = f"{API_BASE}/{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {ACCESS_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} calling {path}")
        print(" ", e.read().decode())
        return None


import urllib.parse  # noqa: E402 (kept near use for clarity)

print("Fetching personal_info...")
info = get("personal_info")
if info:
    print(" ", json.dumps(info, indent=2))

today = datetime.date.today()
week_ago = today - datetime.timedelta(days=7)

print("\nFetching daily_readiness for the last 7 days...")
readiness = get("daily_readiness", {"start_date": week_ago.isoformat(), "end_date": today.isoformat()})
if readiness:
    records = readiness.get("data", [])
    print(f"  {len(records)} record(s) returned")
    for r in records:
        print(f"   {r.get('day')}: readiness score = {r.get('score')}")

print("\nFetching heartrate for the last 24 hours...")
now = datetime.datetime.utcnow()
yesterday = now - datetime.timedelta(hours=24)
hr = get("heartrate", {
    "start_datetime": yesterday.isoformat() + "Z",
    "end_datetime": now.isoformat() + "Z",
})
if hr:
    records = hr.get("data", [])
    print(f"  {len(records)} sample(s) returned")
    if records:
        latest = records[-1]
        print(f"   Most recent: {latest.get('bpm')} bpm at {latest.get('timestamp')}")
