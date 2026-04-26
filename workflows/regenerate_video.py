"""Regenerate video for an existing ad — reuses approved script/copy, only regenerates visuals.
Style-aware: Discovery rows use cinematic_scenes + Ken Burns + mood BGM + OVERLAY_HOOK.
Affiliate rows use Kontext + voiceover + captions + dual PIP + product-matched BGM."""
import re
from core.db import save_ad, supabase
from core.product_scenes import generate_product_scenes
from core.cinematic_scenes import generate_cinematic_scenes
from core.cinematic_video import generate_cinematic_clips
from core.voiceover import generate_voiceover_with_timestamps, get_voiceover_duration
from core.video_assembler import assemble_video


# Inline copies of the helpers from ad_pipeline.py so regenerate doesn't
# import the full pipeline (which transitively pulls every agent).
def _detect_product_type(product_name: str) -> str:
    p = (product_name or "").lower()
    plushie_kw = ["plush", "plushie", "stuffed", "sanrio", "hello kitty",
                  "cinnamoroll", "kuromi", "teddy", "bear", "rattle"]
    building_kw = ["building", "blocks", "lego", "construction set", "warship", "tank"]
    figure_kw = ["anime", "naruto", "one piece", "dragon ball", "luffy", "tanjiro",
                 "zenitsu", "nezuko", "goku", "demon slayer", "jujutsu", "gojo",
                 "pokemon", "my hero", "itachi", "sasuke", "figure", "action figure",
                 "spider man", "spiderman", "transformers", "bumblebee", "gundam", "beyblade"]
    diecast_kw = ["car", "suv", "truck", "die-cast", "diecast", "lightning mcqueen",
                  "land rover", "vehicle", "monster truck", "excavator", "rc car", "drone"]
    if any(k in p for k in plushie_kw): return "plushie"
    if any(k in p for k in building_kw): return "building-blocks"
    if any(k in p for k in figure_kw): return "action-figure"
    if any(k in p for k in diecast_kw): return "die-cast"
    return "generic"


def _pick_discovery_bgm(product_type: str) -> str:
    return {"die-cast": "cinematic", "action-figure": "cinematic",
            "plushie": "soft", "building-blocks": "lofi",
            "generic": "lofi"}.get(product_type, "lofi")


def _pick_affiliate_bgm(product_type: str) -> str:
    return {"die-cast": "cinematic", "action-figure": "cinematic",
            "plushie": "happy", "building-blocks": "lofi",
            "generic": "happy"}.get(product_type, "happy")


def _extract_overlay_hook(copy: str) -> str:
    """Pull OVERLAY_HOOK from a Discovery caption blob. Fallback if missing."""
    m = re.search(r'OVERLAY_HOOK:\s*(.+?)$', copy, re.DOTALL)
    if not m:
        return "Follow for more toy finds"
    text = m.group(1).strip()
    text = re.sub(r'[\U0001F000-\U0001FFFF\U00002600-\U000027BF]', '', text).strip()
    if not text or len(text) > 35:
        return "Follow for more toy finds"
    return text


def run_regenerate_pipeline(ad_id: str, on_step=None):
    """Regenerate the video for an existing ad. Branches on compliance_status:
    - "DISCOVERY" → silent cinematic Ken Burns + mood BGM + OVERLAY_HOOK
    - anything else → Affiliate (Kontext + voiceover + captions + dual PIP)
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
    is_discovery = (ad.get("compliance_status") or "").upper() == "DISCOVERY"
    product_type = _detect_product_type(product)
    print(f"[REGEN] style={'DISCOVERY' if is_discovery else 'AFFILIATE'} product_type={product_type!r}")

    # Find a product image URL (prefer raw product photo, fallback to first scene)
    product_image_url = None
    for url in existing_images:
        if url and ("supabase" in url.lower() or "drive.google.com" in url.lower()
                    or "shopee" in url.lower() or "susercontent" in url.lower()):
            product_image_url = url
            break
    if not product_image_url and existing_images:
        product_image_url = existing_images[0]

    if not product_image_url:
        return {"error": "No product image found in existing ad — cannot regenerate scenes"}

    # ============================================================
    # DISCOVERY BRANCH — silent cinematic, no voiceover, no PIP
    # ============================================================
    if is_discovery:
        _step("Regenerating cinematic scenes...")
        try:
            image_urls = generate_cinematic_scenes(product_image_url,
                                                   num_scenes=4,
                                                   product_type=product_type)
            print(f"[REGEN] Generated {len(image_urls)} cinematic scenes")
        except Exception as e:
            print(f"[REGEN] Cinematic scene gen failed: {e}")
            image_urls = []

        if not image_urls:
            image_urls = [product_image_url]

        # Optional Wan 2.2 Fast motion (off by default = Free mode)
        video_clip_urls = []
        if ad.get("use_ai_video", False):
            _step("Animating cinematic scenes...")
            try:
                video_clip_urls = generate_cinematic_clips(image_urls, duration_per_clip=5)
            except Exception as e:
                print(f"[REGEN] Cinematic animation failed: {e}")
                video_clip_urls = []

        # BGM mood-matched, OVERLAY_HOOK extracted from saved caption
        bgm_style = _pick_discovery_bgm(product_type)
        overlay_hook = _extract_overlay_hook(copy)
        print(f"[REGEN] Discovery BGM: {bgm_style!r}, overlay: {overlay_hook!r}")

        _step("Reassembling discovery video...")
        try:
            video_url = assemble_video(
                image_urls,
                None,                           # NO voiceover
                "",                             # NO script text → no captions burned
                video_clip_urls=video_clip_urls if video_clip_urls else None,
                product_overlay_url=None,       # NO PIP for Discovery
                user_video_urls=None,
                word_timestamps=None,
                bgm_style=bgm_style,
                cta_overlay_text=overlay_hook,
            )
        except Exception as e:
            print(f"[REGEN] Discovery assembly failed: {e}")
            video_url = None

        _step("Saving new video...")
        try:
            updated = {
                "images": ",".join(image_urls) if image_urls else None,
                "voiceover_url": None,
                "video_url": video_url,
            }
            supabase.table("ads").update(updated).eq("id", ad_id).execute()
            print(f"[REGEN] Updated Discovery ad {ad_id}")
        except Exception as e:
            print(f"[REGEN] Could not update ad: {e}")
            updated = {}

        return {**ad, **updated}

    # ============================================================
    # AFFILIATE BRANCH — Kontext scenes + voiceover + captions + PIP
    # ============================================================
    _step("Regenerating product scenes...")
    try:
        image_urls = generate_product_scenes(product_image_url, num_scenes=4)
        print(f"[REGEN] Generated {len(image_urls)} new product scenes")
    except Exception as e:
        print(f"[REGEN] Kontext failed: {e}")
        image_urls = [product_image_url]

    if not image_urls:
        image_urls = [product_image_url]

    _step("Regenerating voiceover...")
    voiceover_url = None
    word_timestamps = None
    try:
        voiceover_url, word_timestamps = generate_voiceover_with_timestamps(copy)
        if voiceover_url:
            duration = get_voiceover_duration(voiceover_url)
            print(f"[REGEN] Voiceover duration: {duration:.1f}s")
    except Exception:
        voiceover_url = None

    affiliate_bgm = _pick_affiliate_bgm(product_type)
    print(f"[REGEN] Affiliate BGM: {affiliate_bgm!r}")

    _step("Reassembling affiliate video...")
    video_url = None
    try:
        video_url = assemble_video(
            image_urls,
            voiceover_url,
            copy,
            product_overlay_url=product_image_url,
            word_timestamps=word_timestamps,
            bgm_style=affiliate_bgm,
        )
    except Exception as e:
        print(f"[REGEN] Affiliate assembly failed: {e}")

    _step("Saving new video...")
    try:
        updated = {
            "images": ",".join(image_urls) if image_urls else None,
            "voiceover_url": voiceover_url,
            "video_url": video_url,
        }
        supabase.table("ads").update(updated).eq("id", ad_id).execute()
        print(f"[REGEN] Updated Affiliate ad {ad_id}")
    except Exception as e:
        print(f"[REGEN] Could not update ad: {e}")
        updated = {}

    return {**ad, **updated}
