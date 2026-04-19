"""Regenerate video for an existing ad — reuses approved script/copy, only regenerates visuals."""
from core.db import save_ad, supabase
from core.product_scenes import generate_product_scenes
from core.voiceover import generate_voiceover_with_timestamps, get_voiceover_duration
from core.video_assembler import assemble_video


def run_regenerate_pipeline(ad_id: str, on_step=None):
    """Regenerate the video for an existing ad.
    Reuses: script, copy, caption, hook, strategy (already approved).
    Regenerates: Kontext product scenes, voiceover, video assembly.
    """

    def _step(name):
        print(f"\n[STEP: {name}]")
        if on_step:
            on_step(name)

    # STEP 1 — Fetch existing ad
    _step("Loading existing ad...")
    try:
        ad = supabase.table("ads").select("*").eq("id", ad_id).single().execute().data
    except Exception as e:
        return {"error": f"Could not load ad: {e}"}

    if not ad:
        return {"error": "Ad not found"}

    product = ad.get("product", "")
    copy = ad.get("copy", "")
    images_str = ad.get("images", "") or ""
    existing_images = [url for url in images_str.split(",") if url.strip()]

    # Find a product image URL (prefer raw product photo, fallback to first scene)
    product_image_url = None
    for url in existing_images:
        if url and "supabase" in url.lower() or "drive.google.com" in url.lower() or "shopee" in url.lower() or "susercontent" in url.lower():
            product_image_url = url
            break
    if not product_image_url and existing_images:
        product_image_url = existing_images[0]

    if not product_image_url:
        return {"error": "No product image found in existing ad — cannot regenerate scenes"}

    # STEP 2 — REGENERATE PRODUCT SCENES via Kontext
    _step("Regenerating product scenes...")
    try:
        image_urls = generate_product_scenes(product_image_url, num_scenes=4)
        print(f"[REGEN] Generated {len(image_urls)} new product scenes")
    except Exception as e:
        print(f"[REGEN] Kontext failed: {e}")
        image_urls = [product_image_url]  # fallback

    if not image_urls:
        image_urls = [product_image_url]

    # STEP 3 — REGENERATE VOICEOVER
    _step("Regenerating voiceover...")
    voiceover_url = None
    voiceover_duration = None
    word_timestamps = None
    try:
        voiceover_url, word_timestamps = generate_voiceover_with_timestamps(copy)
        if voiceover_url:
            voiceover_duration = get_voiceover_duration(voiceover_url)
            print(f"[REGEN] Voiceover duration: {voiceover_duration:.1f}s")
    except Exception:
        voiceover_url = None

    # STEP 4 — ASSEMBLE VIDEO
    _step("Reassembling video...")
    video_url = None
    try:
        video_url = assemble_video(
            image_urls,
            voiceover_url,
            copy,
            product_overlay_url=product_image_url,
            word_timestamps=word_timestamps,
            bgm_style="happy",
        )
    except Exception as e:
        print(f"[REGEN] Video assembly failed: {e}")

    # STEP 5 — UPDATE AD RECORD
    _step("Saving new video...")
    try:
        updated = {
            "images": ",".join(image_urls) if image_urls else None,
            "voiceover_url": voiceover_url,
            "video_url": video_url,
        }
        supabase.table("ads").update(updated).eq("id", ad_id).execute()
        print(f"[REGEN] Updated ad {ad_id}")
    except Exception as e:
        print(f"[REGEN] Could not update ad: {e}")

    # Return full updated ad
    return {**ad, **updated}
