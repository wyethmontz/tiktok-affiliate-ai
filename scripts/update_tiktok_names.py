"""Update TikTok Name (30 char) column based on Pipeline Input column.
Run this after editing any Pipeline Input values in the sheet."""
import sys
import io
import gspread

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

updates = []
for i, row in enumerate(records):
    if i == 0:
        continue
    pipeline_input = row[4] if len(row) > 4 else ''
    current_name = row[9] if len(row) > 9 else ''

    # Skip placeholder rows
    if not pipeline_input.strip() or pipeline_input.startswith('['):
        continue

    # Generate new short name
    new_name = trim_name(pipeline_input)

    # Only update if different
    if new_name != current_name:
        updates.append({'range': f'J{i+1}', 'values': [[new_name]]})
        print(f"Row {i+1}: '{pipeline_input[:40]}' -> '{new_name}'")

if updates:
    for i in range(0, len(updates), 30):
        chunk = updates[i:i+30]
        ws.batch_update(chunk)
    print(f"\nUpdated {len(updates)} TikTok names")
else:
    print("All TikTok names already up to date")
