"""
Convert the JSONL logs from oura_hourly_log.py into flat CSVs for Excel.

Run this once after the hourly collection period is done:
    python oura_tabulate.py

Reads every output/hourly/*.jsonl file, flattens nested dicts (e.g.
"contributors": {"deep_sleep": 74} becomes a "contributors.deep_sleep"
column), and writes output/tabulated/<name>.csv — one row per logged
record, one column per field ever seen across the whole collection period.
Open those CSVs directly in Excel.
"""

import csv
import glob
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IN_DIR = os.path.join(SCRIPT_DIR, "output", "hourly")
OUT_DIR = os.path.join(SCRIPT_DIR, "output", "tabulated")
os.makedirs(OUT_DIR, exist_ok=True)


def flatten(d, prefix=""):
    out = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flatten(v, prefix=f"{key}."))
        elif isinstance(v, list):
            out[key] = json.dumps(v)  # keep arrays as one JSON-string cell rather than exploding columns
        else:
            out[key] = v
    return out


def tabulate_file(jsonl_path):
    rows = []
    with open(jsonl_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(flatten(json.loads(line)))

    if not rows:
        return None

    # Union of all columns ever seen, in first-seen order — computed after
    # reading everything, so no header-mismatch problems across runs where
    # a field only shows up partway through the collection period.
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    name = os.path.splitext(os.path.basename(jsonl_path))[0]
    out_path = os.path.join(OUT_DIR, f"{name}.csv")
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return out_path, len(rows)


def main():
    jsonl_files = glob.glob(os.path.join(IN_DIR, "*.jsonl"))
    if not jsonl_files:
        print(f"No logs found in {IN_DIR} — has oura_hourly_log.py run yet?")
        return
    for path in sorted(jsonl_files):
        result = tabulate_file(path)
        if result:
            out_path, count = result
            print(f"{os.path.basename(path)}: {count} row(s) -> {out_path}")


if __name__ == "__main__":
    main()
