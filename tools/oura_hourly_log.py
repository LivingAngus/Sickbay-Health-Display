"""
Hourly Oura data logger for exploratory review.

Run this once per hour (via a Windows Scheduled Task) for a couple of days
to see what data is actually available and how often each field really
updates, before deciding what the sickbay display should draw down and how
often to poll.

Each run appends one JSON line per record to output/hourly/<name>.jsonl.
JSON Lines rather than CSV on purpose: fields can appear, disappear, or
change shape between runs (e.g. hrv_balance going from null to a real
number), and JSONL tolerates that with zero bookkeeping. Run
oura_tabulate.py afterward to flatten all of this into clean CSVs for Excel.

Endpoints included, and why:
  - daily_readiness, daily_sleep, daily_activity, daily_spo2, daily_stress:
    scored day summaries confirmed working for this account's granted
    scopes.
  - sleep (detailed, NOT daily_sleep): daily_sleep's "contributors" are
    0-100 sub-scores, not the raw readings — e.g. contributors.deep_sleep
    is a normalized score, not minutes. This detailed endpoint is where the
    actual sleep-stage durations (in seconds) live instead.
  - heartrate: logged as a per-pull summary (sample count + latest sample)
    rather than the full sample list each time, to see how many new
    samples show up per hour and how stale the most recent one is.

Not included (confirmed 401 — missing scopes not granted to this app):
  daily_resilience, daily_cardiovascular_age, ring_configuration (which
  would have included battery status). Re-add these if the app is ever
  re-authorized with broader scopes.
"""

import datetime
import json
import os

import oura_client as oura

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(SCRIPT_DIR, "output", "hourly")
os.makedirs(OUT_DIR, exist_ok=True)

NOW = datetime.datetime.utcnow()
PULLED_AT = NOW.isoformat(timespec="seconds") + "Z"

TODAY = datetime.date.today()
WINDOW_START = TODAY - datetime.timedelta(days=5)
DATE_RANGE = {"start_date": WINDOW_START.isoformat(), "end_date": TODAY.isoformat()}

DAILY_ENDPOINTS = [
    "daily_readiness",
    "daily_sleep",
    "daily_activity",
    "daily_spo2",
    "daily_stress",
]


def append_jsonl(filename, record):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "a") as f:
        f.write(json.dumps(record) + "\n")


def log_records(label, path, params=None):
    result = oura.get(path, params)
    if result is None:
        print(f"  {label}: fetch failed (see error above)")
        return
    records = result.get("data", [])
    if not records:
        print(f"  {label}: 0 record(s) in window")
        return
    for rec in records:
        append_jsonl(f"{label}.jsonl", {"pulled_at": PULLED_AT, **rec})
    print(f"  {label}: logged {len(records)} record(s)")


def log_heartrate():
    window_start = NOW - datetime.timedelta(hours=24)
    result = oura.get("heartrate", {
        "start_datetime": window_start.isoformat() + "Z",
        "end_datetime": NOW.isoformat() + "Z",
    })
    samples = (result or {}).get("data", [])
    summary = {
        "pulled_at": PULLED_AT,
        "samples_in_last_24h": len(samples),
        "latest_sample_time": samples[-1]["timestamp"] if samples else None,
        "latest_bpm": samples[-1]["bpm"] if samples else None,
        "latest_source": samples[-1].get("source") if samples else None,
    }
    append_jsonl("heartrate_summary.jsonl", summary)
    print(f"  heartrate: {len(samples)} sample(s) in last 24h, latest at {summary['latest_sample_time']}")


def main():
    print(f"=== Oura hourly log run at {PULLED_AT} ===")
    for path in DAILY_ENDPOINTS:
        log_records(path, path, DATE_RANGE)
    log_records("sleep", "sleep", DATE_RANGE)
    log_heartrate()
    print("Done.\n")


if __name__ == "__main__":
    main()
