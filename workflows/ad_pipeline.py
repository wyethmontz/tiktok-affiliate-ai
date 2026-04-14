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

    # STEP 5 — COMPLIANCE CHECK
    _step("Checking TikTok compliance...")
    original_input_str = f"Product: {input_data['product']}, Audience: {input_data.get('audience', '')}, Goal: {input_data.get('goal', '')}"
    compliance = run_compliance({
        "copy": copy,
        "creative": creative,
        "product": input_data["product"],
        "original_input": original_input_str,
    })

    # Parse compliance status
    compliance_status = "PASS" if "STATUS: PASS" in compliance.upper() else "FAIL"

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

    # STEP 8 — IMAGE GENERATION
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

    # STEP 10 — SAVE TO SUPABASE
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
    }

    save_ad(final_payload)

    return final_payload
