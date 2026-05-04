"""Clean up Supabase ads table:
- Delete ads with broken localhost URLs
- Delete ads older than MAX_AGE_DAYS (default 7 days) to stay under 1GB free tier
"""
import os
import sys
import io
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from supabase import create_client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

MAX_AGE_DAYS = 7  # delete ads older than this

cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

# Step 1: Fast — delete old ads by date (no need to fetch images)
print(f"Deleting ads older than {MAX_AGE_DAYS} days...")
try:
    old_result = sb.table("ads").delete().lt("created_at", cutoff.isoformat()).execute()
    deleted_old = len(old_result.data) if old_result.data else 0
    print(f"  Deleted {deleted_old} old ads")
except Exception as e:
    print(f"  Failed: {e}")
    deleted_old = 0

# Step 2: Page through remaining ads and delete broken localhost URLs
print("\nChecking for broken localhost URLs...")
PAGE_SIZE = 10
offset = 0
deleted_broken = 0
kept = 0

while True:
    result = sb.table("ads").select("id,product,images").range(
        offset, offset + PAGE_SIZE - 1
    ).execute()

    if not result.data:
        break

    for r in result.data:
        images = r.get("images") or ""
        if "localhost" in images or "127.0.0.1" in images:
            sb.table("ads").delete().eq("id", r["id"]).execute()
            print(f"  [BROKEN] Deleted: {r['product'][:50]}")
            deleted_broken += 1
        else:
            kept += 1

    if len(result.data) < PAGE_SIZE:
        break
    offset += PAGE_SIZE

print(f"\n{deleted_broken} deleted (broken URLs)")
print(f"{deleted_old} deleted (older than {MAX_AGE_DAYS} days)")
print(f"{kept} kept (recent + valid)")
