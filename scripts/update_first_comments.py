"""Read TikTok 30-Day Plan Google Sheet and auto-generate first comments for rows with captions."""
import gspread
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SHEET_ID = "1tlMlck70AXHkOOXupk0KgHQarwXg6i9uusWIBhPwNjg"
CREDS_FILE = "google-creds.json"

gc = gspread.service_account(filename=CREDS_FILE)
sh = gc.open_by_key(SHEET_ID)
ws = sh.sheet1
records = ws.get_all_values()

updated = 0
for i, row in enumerate(records):
    if i == 0:
        continue
    caption = row[7] if len(row) > 7 else ""
    first_comment = row[8] if len(row) > 8 else ""

    if caption.strip() and not first_comment.strip():
        lines = [l.strip() for l in caption.split("\n") if l.strip()]
        question = ""
        cta_keyword = "TOY"

        for line in lines:
            kw_match = re.search(r'[Cc]omment\s+(\w+)', line)
            if kw_match:
                cta_keyword = kw_match.group(1).upper()
            if "?" in line and not line.startswith("#"):
                question = line

        if question:
            clean_q = re.sub(r'[\U0001f447\U0001f923\U0001f602\U0001f60d\U0001f525]+\s*$', '', question).strip()
            first_comment_text = f"{clean_q} Comment {cta_keyword} para sa link! \U0001f447"
        else:
            cta_line = lines[0] if lines else caption[:50]
            cta_clean = re.sub(r'#\w+', '', cta_line).strip()
            first_comment_text = f"{cta_clean} \U0001f447"

        row_num = i + 1
        ws.update_cell(row_num, 9, first_comment_text)
        print(f"Row {row_num}: {first_comment_text}")
        updated += 1

if updated == 0:
    print("No rows need first comments — all captions already have comments or no captions yet.")
else:
    print(f"\nUpdated {updated} first comments.")

print(f"\nSheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
