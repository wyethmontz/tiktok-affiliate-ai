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

# Fetch all ads
result = sb.table("ads").select("id,product,images,created_at").execute()

deleted_broken = 0
deleted_old = 0
kept = 0
cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

for r in result.data:
    images = r.get("images") or ""
    created_at_str = r.get("created_at", "")

    # Parse created_at
    try:
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
    except Exception:
        created_at = None

    # Delete if broken localhost URL
    if "localhost" in images or "127.0.0.1" in images:
        sb.table("ads").delete().eq("id", r["id"]).execute()
        print(f"[BROKEN] Deleted: {r['product'][:50]}")
        deleted_broken += 1
        continue

    # Delete if older than MAX_AGE_DAYS
    if created_at and created_at < cutoff:
        sb.table("ads").delete().eq("id", r["id"]).execute()
        print(f"[OLD {(datetime.now(timezone.utc) - created_at).days}d] Deleted: {r['product'][:50]}")
        deleted_old += 1
        continue

    kept += 1

print(f"\n{deleted_broken} deleted (broken URLs)")
print(f"{deleted_old} deleted (older than {MAX_AGE_DAYS} days)")
print(f"{kept} kept (recent + valid)")
