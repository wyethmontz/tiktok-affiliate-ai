"""Check Supabase ads table — what images are stored and if URLs are broken."""
import os
import sys
import io
from dotenv import load_dotenv
from supabase import create_client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

result = sb.table("ads").select("id,product,images,video_url", count="exact").order(
    "created_at", desc=True
).limit(100).execute()

print(f"Total ads in DB: {result.count}")
print()

broken = 0
no_images = 0
for r in result.data:
    images = r.get("images") or ""
    urls = [u for u in images.split(",") if u.strip()]

    if not urls:
        no_images += 1
        continue

    # Flag broken URLs (localhost, expired Replicate URLs)
    is_broken = any("localhost" in u or "127.0.0.1" in u for u in urls)
    if is_broken:
        broken += 1
        print(f"[BROKEN] {r['product'][:50]}")
        print(f"  First URL: {urls[0][:100]}")

print(f"\n{broken} ads have broken localhost URLs (won't load anywhere)")
print(f"{no_images} ads have no images")
print(f"\nRun cleanup_supabase.py to delete broken entries.")
