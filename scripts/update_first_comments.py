"""Sync the TikTok 30-Day Plan Google Sheet:
1. Auto-generate first comments for rows with captions
2. Auto-update TikTok Name (30 char) from Pipeline Input
"""
import gspread
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SHEET_ID = "1tlMlck70AXHkOOXupk0KgHQarwXg6i9uusWIBhPwNjg"
CREDS_FILE = "google-creds.json"


def trim_name(name, max_len=30):
    name = name.strip()
    if len(name) <= max_len:
        return name
    trimmed = name[:max_len].rsplit(' ', 1)[0]
    return trimmed if trimmed else name[:max_len]


gc = gspread.service_account(filename=CREDS_FILE)
sh = gc.open_by_key(SHEET_ID)
ws = sh.sheet1
records = ws.get_all_values()

comment_updates = []
name_updates = []

for i, row in enumerate(records):
    if i == 0:
        continue
    row_num = i + 1
    pipeline_input = row[4] if len(row) > 4 else ""
    caption = row[7] if len(row) > 7 else ""
    first_comment = row[8] if len(row) > 8 else ""
    current_tiktok_name = row[9] if len(row) > 9 else ""

    # 1. UPDATE FIRST COMMENT (if caption exists but comment is empty)
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

        comment_updates.append({'range': f'I{row_num}', 'values': [[first_comment_text]]})
        print(f"[Comment] Row {row_num}: {first_comment_text[:60]}...")

    # 2. UPDATE TIKTOK NAME (if pipeline input exists and name is wrong/empty)
    if pipeline_input.strip() and not pipeline_input.startswith('['):
        new_name = trim_name(pipeline_input)
        if new_name != current_tiktok_name:
            name_updates.append({'range': f'J{row_num}', 'values': [[new_name]]})
            print(f"[Name] Row {row_num}: '{pipeline_input[:40]}' -> '{new_name}'")

# Apply updates in batches
all_updates = comment_updates + name_updates
if all_updates:
    for i in range(0, len(all_updates), 30):
        chunk = all_updates[i:i+30]
        ws.batch_update(chunk)

print(f"\n{len(comment_updates)} first comments updated")
print(f"{len(name_updates)} TikTok names updated")
print(f"\nSheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
