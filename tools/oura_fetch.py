"""
Pull a configurable set of data types from the Oura API.

To change what gets downloaded, edit the DATA_REQUESTS list below — nothing
else in this file needs to change. Each entry is:
    (friendly label, API endpoint path, query params dict or None)

Token refresh is handled automatically by oura_client.get(), including on
a rotated/expired access token.
"""

import datetime
import json

import oura_client as oura

TODAY = datetime.date.today()
WEEK_AGO = TODAY - datetime.timedelta(days=7)
NOW = datetime.datetime.utcnow()
YESTERDAY = NOW - datetime.timedelta(hours=24)

DATE_RANGE = {"start_date": WEEK_AGO.isoformat(), "end_date": TODAY.isoformat()}

# --- Edit this list to change what gets pulled -----------------------------
DATA_REQUESTS = [
    ("Personal info",    "personal_info",   None),
    ("Daily readiness",  "daily_readiness", DATE_RANGE),
    ("Daily sleep",      "daily_sleep",     DATE_RANGE),
    ("Daily activity",   "daily_activity",  DATE_RANGE),
    ("Daily SpO2",       "daily_spo2",      DATE_RANGE),
    ("Heart rate (24h)", "heartrate",       {
        "start_datetime": YESTERDAY.isoformat() + "Z",
        "end_datetime": NOW.isoformat() + "Z",
    }),
    # Add more here, e.g.:
    # ("Workouts", "workout", DATE_RANGE),
    # ("Sessions", "session", DATE_RANGE),
    # ("Stress",   "daily_stress", DATE_RANGE),
]
# ----------------------------------------------------------------------------


def main():
    for label, path, params in DATA_REQUESTS:
        print(f"\n=== {label} ({path}) ===")
        result = oura.get(path, params)
        if result is None:
            continue
        text = json.dumps(result, indent=2)
        print(text[:2000] + ("... (truncated)" if len(text) > 2000 else ""))


if __name__ == "__main__":
    main()
