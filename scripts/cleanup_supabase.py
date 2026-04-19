"""Delete ads with broken localhost URLs from Supabase."""
import os
import sys
import io
from dotenv import load_dotenv
from supabase import create_client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Fetch all ads
result = sb.table("ads").select("id,product,images,created_at").execute()

deleted = 0
kept = 0

for r in result.data:
    images = r.get("images") or ""
    # Delete if images column references localhost (won't work on any other device)
    if "localhost" in images or "127.0.0.1" in images:
        sb.table("ads").delete().eq("id", r["id"]).execute()
        print(f"Deleted: {r['product'][:50]}")
        deleted += 1
    else:
        kept += 1

print(f"\nDeleted {deleted} ads with broken localhost URLs")
print(f"Kept {kept} ads with good URLs")
