"""
update_30day_plan.py

Re-tags the TikTok 30-Day Plan Google Sheet for the dual-pipeline strategy
(Discovery + Affiliate). Runs in dry-run mode by default — pass --apply to
actually write.

Rules (locked with user 2026-04-21):
  - Time-slot based tagging:
      12:00 PM  -> Discovery
      6:00 PM   -> Discovery
      9:00 PM   -> Affiliate
  - Ratio per day: 2 Discovery + 1 Affiliate  (1:2)
  - Blank columns H (Caption) + I (First Comment) on Discovery rows so the
    pipeline regenerates them via discovery_copywriter.
  - Adds column L "Post_Style" with values "Affiliate" or "Discovery"
  - Already-Posted rows are skipped (never overwritten)
  - A timestamped CSV backup is written to scripts/backups/ before any write.

Usage (from project root):
  python scripts/update_30day_plan.py              # dry-run (default)
  python scripts/update_30day_plan.py --apply      # actually write

Prereqs:
  - google-creds.json in project root (service account with edit access)
  - gspread installed (pip install gspread)

Security notes:
  - google-creds.json is the service account key. Keep it gitignored.
  - Script only writes to cells L* (Post_Style), H* (Caption), I* (First Comment).
    It never reads the creds into logs, never pushes anywhere else, never emails.
  - Batch writes used (single API call) to minimize retry risk.
"""
import argparse
import csv
import io
import os
import sys
from datetime import datetime

import gspread

# ---- Hard-coded plan parameters (locked with user) ----
SHEET_ID = "1tlMlck70AXHkOOXupk0KgHQarwXg6i9uusWIBhPwNjg"
CREDS_FILE = "google-creds.json"
BACKUP_DIR = os.path.join("scripts", "backups")

TIME_TO_STYLE = {
    "12:00": "Discovery",
    "6:00":  "Discovery",
    "9:00":  "Affiliate",
}

POST_STYLE_HEADER = "Post_Style"
POST_STYLE_COL = 7    # Column G (moved adjacent to Status for readability)

# Column layout after the Post_Style insert at G:
# A Date | B Day | C Time | D Shopee Search | E Pipeline Input | F Status
# G Post_Style | H Views | I TikTok Caption | J First Comment | K TikTok Name | L Notes
CAPTION_COL = 9       # Column I (was H before Post_Style insert)
FIRST_COMMENT_COL = 10 # Column J (was I before Post_Style insert)
STATUS_COL = 6        # Column F
TIME_COL = 3          # Column C


def classify_time(time_str: str) -> str | None:
    """Return 'Discovery' / 'Affiliate' for known time-slot prefixes, else None."""
    t = (time_str or "").strip().upper()
    for prefix, style in TIME_TO_STYLE.items():
        if t.startswith(prefix):
            return style
    return None


def col_letter(col_idx: int) -> str:
    """1-indexed column number -> letter (1=A, 12=L, etc.)"""
    letters = ""
    n = col_idx
    while n > 0:
        n, r = divmod(n - 1, 26)
        letters = chr(65 + r) + letters
    return letters


def cell_ref(row: int, col: int) -> str:
    return f"{col_letter(col)}{row}"


def backup_sheet(rows: list[list[str]]) -> str:
    """Write current sheet state to a timestamped CSV. Returns backup path."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BACKUP_DIR, f"30day_plan_backup_{ts}.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(rows)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Actually write to the sheet. Default is dry-run.")
    args = parser.parse_args()

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

    print("=== 30-Day Plan Re-Tag Script ===")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print(f"Sheet: {SHEET_ID}")
    print()

    # ---- Load sheet ----
    gc = gspread.service_account(filename=CREDS_FILE)
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.sheet1
    rows = ws.get_all_values()
    header = rows[0] if rows else []
    print(f"Loaded {len(rows)} rows (including header).")
    print(f"Current header ({len(header)} cols): {header}")
    print()

    # ---- Local CSV backup (always, even in dry-run — cheap insurance) ----
    backup_path = backup_sheet(rows)
    print(f"Backup written: {backup_path}")
    print()

    # ---- Build batch of updates ----
    updates: list[dict] = []
    summary = {
        "discovery_tagged": 0,
        "affiliate_tagged": 0,
        "captions_blanked": 0,
        "skipped_posted": 0,
        "skipped_unknown_time": 0,
    }

    # Header in L1
    if len(header) < POST_STYLE_COL or header[POST_STYLE_COL - 1] != POST_STYLE_HEADER:
        updates.append({
            "range": cell_ref(1, POST_STYLE_COL),
            "values": [[POST_STYLE_HEADER]],
        })
        print(f"Will set {cell_ref(1, POST_STYLE_COL)} header to '{POST_STYLE_HEADER}'")

    # Walk data rows (skip header; rows[0] is header, so data rows are 1-indexed from 2)
    for idx, row in enumerate(rows[1:], start=2):
        status = (row[STATUS_COL - 1] if len(row) >= STATUS_COL else "").strip().lower()
        time_str = row[TIME_COL - 1] if len(row) >= TIME_COL else ""
        pipeline_input = row[4] if len(row) > 4 else ""

        if status.startswith("posted"):
            summary["skipped_posted"] += 1
            continue

        style = classify_time(time_str)
        if not style:
            summary["skipped_unknown_time"] += 1
            print(f"  Row {idx}: unknown time '{time_str}' — SKIPPED")
            continue

        # Tag L column
        updates.append({
            "range": cell_ref(idx, POST_STYLE_COL),
            "values": [[style]],
        })

        if style == "Discovery":
            summary["discovery_tagged"] += 1
            # Blank H (caption) + I (first comment) for regeneration
            updates.append({
                "range": cell_ref(idx, CAPTION_COL),
                "values": [[""]],
            })
            updates.append({
                "range": cell_ref(idx, FIRST_COMMENT_COL),
                "values": [[""]],
            })
            summary["captions_blanked"] += 1
        else:
            summary["affiliate_tagged"] += 1

        short_name = (pipeline_input[:32] + "...") if len(pipeline_input) > 32 else pipeline_input
        print(f"  Row {idx}: {time_str:10} -> {style:9}  ({short_name})")

    # ---- Summary ----
    print()
    print("=== Planned changes ===")
    print(f"  Discovery tagged:       {summary['discovery_tagged']}")
    print(f"  Affiliate tagged:       {summary['affiliate_tagged']}")
    print(f"  Discovery captions blanked (H+I): {summary['captions_blanked']}")
    print(f"  Posted rows skipped (untouched):  {summary['skipped_posted']}")
    print(f"  Unknown time rows skipped:        {summary['skipped_unknown_time']}")
    print(f"  Total batch ops: {len(updates)}")
    print()

    if not args.apply:
        print("DRY-RUN complete. No changes written.")
        print("Re-run with --apply to commit.")
        return

    if not updates:
        print("No updates to apply.")
        return

    # ---- Execute batch ----
    print(f"Writing {len(updates)} updates to sheet...")
    ws.batch_update(updates, value_input_option="USER_ENTERED")
    print("Sheet updated successfully.")
    print(f"Backup saved at: {backup_path}")


if __name__ == "__main__":
    main()
