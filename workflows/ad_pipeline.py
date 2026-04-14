import json
import re
from agents.strategist import run_strategist
from agents.copywriter import run_copywriter
from agents.creative import run_creative
from agents.qa import run_qa
from agents.media import run_media
from agents.compliance import run_compliance
from agents.optimizer import run_optimizer
from core.db import save_ad
from core.image_gen import generate_images
from core.voiceover import generate_voiceover
from core.llm import call_claude

MAX_COMPLIANCE_RETRIES = 2

def _fix_copy(copy, compliance_feedback, input_data):
    """Send the failed copy back to AI with compliance issues to auto-fix."""
    prompt = f"""You are a TikTok content creator. Your script was flagged for compliance issues.

ORIGINAL SCRIPT:
{copy}

COMPLIANCE ISSUES FOUND:
{compliance_feedback}

PRODUCT (only facts you can use): {input_data.get('product', '')}
AUDIENCE: {input_data.get('audience', '')}

Rewrite the script to fix ALL the issues above. Keep the same tone, format, and language (Tagalog).

RULES:
- Remove any fabricated claims, prices, or statistics
- Remove any fake testimonials or social proof
- Remove any fake urgency
- Make sure CTA includes #ad disclosure
- Only describe what the product actually does based on the product name
- Keep it 60-100 words, same TikTok style

Return in this format:

SCRIPT:
[fixed TikTok script]

CTA:
[fixed call-to-action with #ad]

HASHTAGS:
[5-8 hashtags including #ad]
"""
    return call_claude(prompt)


def run_pipeline(input_data, on_step=None):

    def _step(name):
        print(f"\n[STEP: {name}]")
        if on_step:
            on_step(name)

    # STEP 0 — OPTIMIZER (learn from past ads)
    _step("Analyzing past ad performance...")
    try:
        insights = run_optimizer()
    except Exception:
        insights = None

    # STEP 1 — STRATEGIST
    _step("Creating TikTok strategy...")
    strategy_raw = run_strategist(input_data, insights=insights)

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

    # STEP 3 — COPYWRITER
    _step("Writing TikTok script...")
    copywriter_input = {
        **strategy,
        "audience": input_data.get("audience", ""),
        "product": input_data["product"],
    }
    copy = run_copywriter(copywriter_input)

    # STEP 4 — CREATIVE DIRECTOR
    _step("Planning visual scenes...")
    creative = run_creative({
        "script": copy,
        "tiktok_format": strategy.get("tiktok_format", ""),
    })

    # STEP 5 — COMPLIANCE CHECK + AUTO-FIX LOOP
    original_input_str = f"Product: {input_data['product']}, Audience: {input_data.get('audience', '')}, Goal: {input_data.get('goal', '')}"
    compliance_status = "FAIL"

    for attempt in range(1, MAX_COMPLIANCE_RETRIES + 2):  # 1 initial + 2 retries
        _step(f"Checking TikTok compliance (attempt {attempt})...")
        compliance = run_compliance({
            "copy": copy,
            "creative": creative,
            "product": input_data["product"],
            "original_input": original_input_str,
        })

        compliance_status = "PASS" if "STATUS: PASS" in compliance.upper() else "FAIL"

        if compliance_status == "PASS":
            print(f"[COMPLIANCE] Passed on attempt {attempt}")
            break

        if attempt <= MAX_COMPLIANCE_RETRIES:
            _step(f"Auto-fixing compliance issues (attempt {attempt})...")
            print(f"[COMPLIANCE] Failed — auto-fixing...")
            copy = _fix_copy(copy, compliance, input_data)

            # Re-run creative director with fixed copy
            _step("Re-planning visual scenes...")
            creative = run_creative({
                "script": copy,
                "tiktok_format": strategy.get("tiktok_format", ""),
            })
        else:
            print(f"[COMPLIANCE] Still failing after {MAX_COMPLIANCE_RETRIES} retries — saving with FAIL status")

    # STEP 6 — QA CHECK
    _step("Running QA evaluation...")
    qa = run_qa({
        "content": creative
    })

    # STEP 7 — MEDIA PROMPTS
    _step("Creating image prompts...")
    media = run_media({
        "scenes": creative
    })

    # STEP 8 — IMAGE GENERATION (or use provided product images)
    product_image_urls = input_data.get("product_image_urls", [])

    if product_image_urls:
        _step("Using provided product images...")
        image_urls = product_image_urls
    else:
        _step("Generating TikTok images...")
        try:
            image_urls = generate_images(media)
        except Exception:
            image_urls = []

    # STEP 9 — VOICEOVER
    _step("Generating voiceover...")
    try:
        voiceover_url = generate_voiceover(copy)
    except Exception:
        voiceover_url = None

    # STEP 10 — GENERATE TIKTOK CAPTION
    _step("Creating TikTok caption...")
    # Extract CTA and hashtags from copy
    cta_match = re.search(r'CTA:\s*(.+?)(?:HASHTAGS:|$)', copy, re.DOTALL)
    hashtag_match = re.search(r'HASHTAGS:\s*(.+?)$', copy, re.DOTALL)
    cta_text = cta_match.group(1).strip() if cta_match else ""
    hashtags = hashtag_match.group(1).strip() if hashtag_match else "#ad #TikTokShop #fyp"
    # Ensure AIGC disclosure is in hashtags
    if "#AIgenerated" not in hashtags.lower().replace(" ", ""):
        hashtags = hashtags.rstrip() + " #AIgenerated"
    if "#ad" not in hashtags.lower():
        hashtags = "#ad " + hashtags
    tiktok_caption = f"{cta_text}\n\n{hashtags}".strip()

    # STEP 11 — SAVE TO SUPABASE
    _step("Saving to database...")

    score_match = re.search(r'\d+', qa or "")
    qa_numeric = int(score_match.group()) if score_match else None

    final_payload = {
        "product": input_data["product"],
        "audience": input_data.get("audience", ""),
        "platform": "TikTok",
        "goal": input_data.get("goal", ""),
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
    }

    save_ad(final_payload)

    return final_payload
