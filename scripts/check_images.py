"""Check Supabase ads table — what images are stored and if URLs are broken."""
import os
import sys
import io
from dotenv import load_dotenv
from supabase import create_client

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Page through in small chunks to avoid timeout on huge base64 blobs
PAGE_SIZE = 10
offset = 0
broken = 0
no_images = 0
total = 0

while True:
    result = sb.table("ads").select("id,product,images").order(
        "created_at", desc=True
    ).range(offset, offset + PAGE_SIZE - 1).execute()

    if not result.data:
        break

    for r in result.data:
        total += 1
        images = r.get("images") or ""
        urls = [u for u in images.split(",") if u.strip()]

        if not urls:
            no_images += 1
            continue

        # Flag broken URLs (localhost only — Replicate URLs expire too but work as long as kept)
        is_broken = any("localhost" in u or "127.0.0.1" in u for u in urls)
        if is_broken:
            broken += 1
            print(f"[BROKEN] {r['product'][:50]}")
            print(f"  First URL: {urls[0][:100]}")

    if len(result.data) < PAGE_SIZE:
        break
    offset += PAGE_SIZE

print(f"\nScanned {total} ads")
print(f"{broken} have broken localhost URLs")
print(f"{no_images} have no images")
print(f"\nRun cleanup_supabase.py to delete broken entries.")
