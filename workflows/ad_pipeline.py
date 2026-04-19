import json
import re
from agents.strategist import run_strategist
from agents.copywriter import run_copywriter
from agents.creative import run_creative
from agents.qa import run_qa
from agents.media import run_media
from agents.compliance import run_compliance
from agents.optimizer import run_optimizer
from core.db import save_ad, supabase
from core.image_gen import generate_images
from core.product_scenes import generate_product_scenes
from core.policy_checker import get_latest_rules
from core.video_gen import generate_video_clips
from core.voiceover import generate_voiceover
from core.llm import call_claude
from core.video_assembler import assemble_video

MAX_COMPLIANCE_RETRIES = 4

def _fix_copy(copy, compliance_feedback, input_data, attempt=1):
    """Send the failed copy back to AI with compliance issues to auto-fix.
    Escalates approach on each attempt — gentle fix first, full rewrite last."""

    product = input_data.get('product', '')
    audience = input_data.get('audience', '')

    if attempt <= 2:
        # Attempts 1-2: fix the specific issues
        prompt = f"""You are a TikTok content creator. Your script was flagged for compliance issues.

ORIGINAL SCRIPT:
{copy}

COMPLIANCE ISSUES FOUND:
{compliance_feedback}

PRODUCT (only facts you can use): {product}
AUDIENCE: {audience}

Rewrite the script to fix ALL the issues above. Keep the same tone, format, and language (Tagalog).

RULES:
- Remove any fabricated claims, prices, or statistics
- Remove any fake testimonials or social proof
- Remove any fake urgency
- Make sure CTA includes #ad disclosure
- Only describe what the product actually does based on the product name
- Keep it 30-40 words MAXIMUM (must fit a 14-second video, count your words)
- Do NOT use apostrophe contractions ('to, 'yan, 'yung, 'di) — write full words: ito, iyan, iyong, hindi

Return in this format:

SCRIPT:
[fixed TikTok script]

CTA:
[comment-based CTA with #ad]

ENGAGEMENT QUESTION:
[a "this or that" question to drive comments]

HASHTAGS:
[5-8 hashtags including #ad #ToysPH #BudolFinds]
"""
    else:
        # Attempts 3+: write a completely new script from scratch
        prompt = f"""You are a TikTok content creator. Previous scripts for this product kept failing compliance checks.

FORGET the previous script. Write a BRAND NEW script from scratch.

PRODUCT: {product}
AUDIENCE: {audience}

STRICT RULES (every previous script broke these — do NOT repeat):
- ZERO fabricated claims — no prices, stats, percentages, or reviews you made up
- ZERO fake urgency — no "limited stocks", "selling out", "last chance"
- ZERO health/beauty/miracle claims
- ONLY describe what the product IS based on its name — nothing more
- CTA MUST include #ad
- Keep it simple: show excitement about the product without lying
- 30-40 words MAXIMUM in Tagalog (natural spoken, not formal — count your words)
- Do NOT use apostrophe contractions ('to, 'yan, 'yung, 'di) — write full words: ito, iyan, iyong, hindi
- If the product is a toy, use words like "toy", "model", or "collectible"

Write something safe and simple — better to be boring and compliant than creative and flagged.

Return in this format:

SCRIPT:
[brand new safe TikTok script in Tagalog]

CTA:
[comment-based CTA with #ad]

ENGAGEMENT QUESTION:
[a "this or that" question to drive comments]

HASHTAGS:
[5-8 hashtags including #ad #ToysPH #BudolFinds]
"""
    return call_claude(prompt)


def run_pipeline(input_data, on_step=None):

    def _step(name):
        print(f"\n[STEP: {name}]")
        if on_step:
            on_step(name)

    # STEP 0 — FETCH LATEST TIKTOK RULES (cached 24h)
    _step("Checking latest TikTok policies...")
    try:
        latest_rules = get_latest_rules()
    except Exception:
        latest_rules = None

    # STEP 1 — OPTIMIZER (learn from past ads)
    _step("Analyzing past ad performance...")
    try:
        insights = run_optimizer()
    except Exception:
        insights = None

    # Fetch recent hooks from ALL ads to avoid repetitive patterns across products
    past_hooks = []
    try:
        recent_ads = supabase.table("ads").select("hook").order(
            "created_at", desc=True
        ).limit(10).execute().data
        past_hooks = [a.get("hook", "") for a in recent_ads if a.get("hook")]
        if past_hooks:
            print(f"[PIPELINE] Found {len(past_hooks)} recent hooks — will avoid repeating patterns")
    except Exception:
        pass

    # STEP 2 — STRATEGIST
    _step("Creating TikTok strategy...")
    # Pass past hooks so strategist picks a different style
    input_data_for_strategy = {**input_data, "past_hooks": past_hooks}
    strategy_raw = run_strategist(input_data_for_strategy, insights=insights)

    print("\n[RAW STRATEGIST OUTPUT]\n")
    print(strategy_raw)

    # STEP 2 — PARSE JSON
    cleaned = re.sub(r"```(?:json)?\s*", "", strategy_raw).strip()
    json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    try:
        strategy = json.loads(json_match.group() if json_match else cleaned)
    except (json.JSONDecodeError, AttributeError):
        print("\nERROR: AI did not return valid JSON")
        print("Cleaned output was:", cleaned)
        return {"error": "AI did not return valid JSON", "raw": strategy_raw}

    # Use auto-detected audience/goal if user didn't provide them
    audience = input_data.get("audience", "") or strategy.get("auto_audience", "TikTok users")
    goal = input_data.get("goal", "") or strategy.get("auto_goal", "Boost engagement and drive clicks")
    print(f"[PIPELINE] Audience: {audience}")
    print(f"[PIPELINE] Goal: {goal}")

    # STEP 3 — COPYWRITER
    _step("Writing TikTok script...")
    copywriter_input = {
        **strategy,
        "audience": audience,
        "product": input_data["product"],
        "past_hooks": past_hooks,
    }
    copy = run_copywriter(copywriter_input)

    # STEP 4 — CREATIVE DIRECTOR
    product_image_urls = input_data.get("product_image_urls", [])
    has_product_images = bool(product_image_urls)

    _step("Planning visual scenes...")
    creative = run_creative({
        "script": copy,
        "tiktok_format": strategy.get("tiktok_format", ""),
        "has_product_images": has_product_images,
    })

    # STEP 5 — COMPLIANCE CHECK + AUTO-FIX LOOP
    original_input_str = f"Product: {input_data['product']}, Audience: {audience}, Goal: {goal}"
    compliance_status = "FAIL"

    for attempt in range(1, MAX_COMPLIANCE_RETRIES + 2):  # 1 initial + N retries
        _step(f"Checking TikTok compliance (attempt {attempt})...")
        compliance = run_compliance({
            "copy": copy,
            "creative": creative,
            "product": input_data["product"],
            "original_input": original_input_str,
            "latest_rules": latest_rules or "",
        })

        compliance_status = "PASS" if "STATUS: PASS" in compliance.upper() else "FAIL"

        if compliance_status == "PASS":
            print(f"[COMPLIANCE] Passed on attempt {attempt}")
            break

        if attempt <= MAX_COMPLIANCE_RETRIES:
            if attempt <= 2:
                _step(f"Fixing compliance issues (attempt {attempt})...")
                print(f"[COMPLIANCE] Failed — fixing specific issues...")
            else:
                _step(f"Rewriting script from scratch (attempt {attempt})...")
                print(f"[COMPLIANCE] Failed {attempt}x — writing brand new script...")

            copy = _fix_copy(copy, compliance, input_data, attempt=attempt)

            # Only re-run creative director on fresh rewrites (attempt 3+)
            if attempt >= 3:
                _step("Re-planning visual scenes...")
                creative = run_creative({
                    "script": copy,
                    "tiktok_format": strategy.get("tiktok_format", ""),
                    "has_product_images": has_product_images,
                })
        else:
            print(f"[COMPLIANCE] Still failing after {MAX_COMPLIANCE_RETRIES} retries — stopping pipeline to save costs")
            _step("Compliance failed — stopping pipeline")
            return {
                "error": "Script failed TikTok compliance after multiple rewrites. Try a different product name or simpler description.",
                "compliance_status": "FAIL",
                "copy": copy,
                "compliance_feedback": compliance,
                "product": input_data["product"],
            }

    # STEP 6 — QA CHECK
    _step("Running QA evaluation...")
    qa = run_qa({
        "content": creative
    })

    # STEP 7 — DETERMINE CONTENT MODE
    user_video_urls = input_data.get("user_video_urls", [])
    has_user_videos = bool(user_video_urls)
    media = ""
    image_urls = []
    video_clip_urls = []

    if has_user_videos:
        # USER VIDEO MODE — real phone recordings, skip all AI image/video gen
        _step("Using your video clips...")
        print(f"[PIPELINE] User provided {len(user_video_urls)} video clips — skipping AI image/video generation")
    elif has_product_images:
        # KONTEXT MODE — generate realistic in-use scenes from product photo
        _step("Generating realistic product scenes...")
        try:
            image_urls = generate_product_scenes(product_image_urls[0], num_scenes=4)
            print(f"[PIPELINE] Generated {len(image_urls)} realistic product scenes via Kontext")
        except Exception as e:
            print(f"[PIPELINE] Kontext failed ({e}), falling back to raw product photos")
            image_urls = []

        # Fallback: if Kontext generated nothing, use raw product photos
        if not image_urls:
            print(f"[PIPELINE] Using raw product photos as fallback")
            image_urls = product_image_urls
    else:
        # AI MODE — generate everything
        _step("Creating image prompts...")
        media = run_media({
            "scenes": creative,
            "has_product_images": False,
        })

        _step("Generating TikTok images...")
        try:
            image_urls = generate_images(media)
            image_urls = [url for url in image_urls if url is not None]
        except Exception:
            image_urls = []
        print(f"[PIPELINE] Generated {len(image_urls)} AI images")

    # STEP 8 — VOICEOVER WITH TIMESTAMPS (for synced captions)
    _step("Generating voiceover...")
    voiceover_url = None
    voiceover_duration = None
    word_timestamps = None
    try:
        from core.voiceover import get_voiceover_duration, generate_voiceover_with_timestamps
        voiceover_url, word_timestamps = generate_voiceover_with_timestamps(copy)
        if voiceover_url:
            voiceover_duration = get_voiceover_duration(voiceover_url)
            print(f"[PIPELINE] Voiceover duration: {voiceover_duration:.1f}s")
            if word_timestamps:
                print(f"[PIPELINE] Got {len(word_timestamps)} word timestamps for synced captions")
    except Exception:
        voiceover_url = None

    # STEP 9 — VIDEO CLIP GENERATION (optional — off by default to save costs)
    use_ai_video = input_data.get("use_ai_video", False)
    if use_ai_video and not has_user_videos and image_urls:
        _step("Generating AI motion video clips...")
        try:
            video_clip_urls = generate_video_clips(image_urls, media,
                                                   target_duration=voiceover_duration)
            print(f"[PIPELINE] Generated {len(video_clip_urls)}/{len(image_urls)} video clips")
        except Exception:
            video_clip_urls = []
    elif not has_user_videos:
        print(f"[PIPELINE] Using free FFmpeg video mode (AI video gen disabled)")

    # STEP 10 — VIDEO ASSEMBLY
    _step("Assembling TikTok video...")
    product_overlay = product_image_urls[0] if product_image_urls else None
    try:
        video_url = assemble_video(image_urls, voiceover_url, copy,
                                   video_clip_urls=video_clip_urls if video_clip_urls else None,
                                   product_overlay_url=product_overlay,
                                   user_video_urls=user_video_urls if has_user_videos else None,
                                   word_timestamps=word_timestamps,
                                   bgm_style=input_data.get("bgm_style", "lofi"))
    except Exception:
        video_url = None

    # STEP 12 — GENERATE TIKTOK CAPTION
    _step("Creating TikTok caption...")
    # Extract CTA, engagement question, and hashtags
    cta_match = re.search(r'CTA:\s*(.+?)(?:ENGAGEMENT QUESTION:|HASHTAGS:|$)', copy, re.DOTALL)
    engagement_match = re.search(r'ENGAGEMENT QUESTION:\s*(.+?)(?:HASHTAGS:|$)', copy, re.DOTALL)
    hashtag_match = re.search(r'HASHTAGS:\s*(.+?)$', copy, re.DOTALL)
    cta_text = cta_match.group(1).strip() if cta_match else ""
    engagement_q = engagement_match.group(1).strip() if engagement_match else ""
    hashtags = hashtag_match.group(1).strip() if hashtag_match else "#ad #ToysPH #BudolFinds"

    # Deduplicate: collect all unique hashtags from CTA + HASHTAGS section
    all_tags = re.findall(r'#\w+', f"{cta_text} {hashtags}")
    seen = set()
    unique_tags = []
    for tag in all_tags:
        tag_lower = tag.lower()
        if tag_lower not in seen:
            seen.add(tag_lower)
            unique_tags.append(tag)

    # Ensure required tags are present
    if "#ad" not in {t.lower() for t in unique_tags}:
        unique_tags.insert(0, "#ad")
    if "#aigenerated" not in {t.lower() for t in unique_tags}:
        unique_tags.append("#AIgenerated")

    # Inject PH niche tags if missing
    for tag in ["#ToysPH", "#DiecastPH", "#TikTokShopPH"]:
        if tag.lower() not in seen:
            unique_tags.insert(1, tag)
            seen.add(tag.lower())

    hashtags = " ".join(unique_tags)

    # Build caption: CTA + engagement question + hashtags
    cta_clean = re.sub(r'#\w+', '', cta_text).strip()
    parts = [p for p in [cta_clean, engagement_q, hashtags] if p]
    tiktok_caption = "\n\n".join(parts).strip()

    # STEP 13 — SAVE TO SUPABASE
    _step("Saving to database...")

    score_match = re.search(r'\d+', qa or "")
    qa_numeric = int(score_match.group()) if score_match else None

    final_payload = {
        "product": input_data["product"],
        "audience": audience,
        "platform": "TikTok",
        "goal": goal,
        "hook": strategy.get("hook", ""),
        "angle": strategy.get("angle", ""),
        "positioning": strategy.get("positioning", ""),
        "copy": copy,
        "creative": creative,
        "qa_score": qa,
        "qa_score_numeric": qa_numeric,
        "media": media,
        "images": ",".join(image_urls) if image_urls else None,
        "voiceover_url": voiceover_url,
        "compliance_status": compliance_status,
        "tiktok_caption": tiktok_caption,
        "video_url": video_url,
    }

    # Save and include the returned ID so frontend can regenerate
    response = save_ad(final_payload)
    if response and response.data and len(response.data) > 0:
        final_payload["id"] = response.data[0].get("id")

    return final_payload
