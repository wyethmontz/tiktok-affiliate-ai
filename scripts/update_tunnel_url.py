"""Write Cloudflare tunnel URLs to a 'Mobile Access' tab in the Google Sheet
so you can copy-paste it on your phone."""
import sys
import io
import gspread
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SHEET_ID = "1tlMlck70AXHkOOXupk0KgHQarwXg6i9uusWIBhPwNjg"
CREDS_FILE = "google-creds.json"
TAB_NAME = "Mobile Access"

if len(sys.argv) < 3:
    print("Usage: python update_tunnel_url.py <frontend_url> <backend_url>")
    sys.exit(1)

frontend_url = sys.argv[1]
backend_url = sys.argv[2]

gc = gspread.service_account(filename=CREDS_FILE)
sh = gc.open_by_key(SHEET_ID)

# Create or get the Mobile Access tab
try:
    ws = sh.worksheet(TAB_NAME)
    ws.clear()
except gspread.WorksheetNotFound:
    ws = sh.add_worksheet(title=TAB_NAME, rows=10, cols=3)

# Write the URLs with timestamp
now = datetime.now().strftime("%Y-%m-%d %H:%M")
rows = [
    ["TikTok Affiliate AI - Mobile Access"],
    [""],
    ["Updated:", now],
    [""],
    ["FRONTEND URL (open on phone):"],
    [frontend_url],
    [""],
    ["Backend URL (reference):"],
    [backend_url],
]

ws.update("A1", rows)

# Make the frontend URL cell big/bold so it's easy to copy on phone
ws.format("A1", {
    "textFormat": {"bold": True, "fontSize": 14, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
    "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
})
ws.format("A5", {
    "textFormat": {"bold": True, "fontSize": 12},
    "backgroundColor": {"red": 1, "green": 0.85, "blue": 0.85},
})
ws.format("A6", {
    "textFormat": {"bold": True, "fontSize": 13, "foregroundColor": {"red": 0, "green": 0.3, "blue": 0.8}},
})

print(f"Updated sheet: Frontend URL = {frontend_url}")
print(f"View on phone: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=")
