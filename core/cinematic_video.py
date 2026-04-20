"""
Cinematic video generator — Wan 2.2 I2V Fast (Replicate).
Cheaper alternative to Wan 2.5 used in the affiliate path. ~$0.05 per 5s clip.
"""
import os
import re
import time
import random
import httpx
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
WAN_URL = "https://api.replicate.com/v1/models/wan-video/wan-2.2-i2v-fast/predictions"

# Motion variety pool — a randomized sample is drawn per run so a 30-day
# Discovery campaign doesn't reuse the same camera move.
MOTION_POOL = [
    "smooth cinematic camera push-in, product stays sharp, minimal warping",
    "slow horizontal pan across the product details, product stays sharp",
    "subtle orbital rotation around the product, product stays sharp",
    "gentle crane shot moving from top-down to heroic angle, product stays sharp",
    "macro slow-zoom on the most intricate parts, product stays sharp",
    "dynamic tilt-up from the base to the top, product stays sharp",
]

# Retained for callers that pass no motion_prompts AND don't want randomization.
DEFAULT_MOTION_PROMPT = MOTION_POOL[0]


def get_varied_motion(count: int = 4) -> list[str]:
    """Draw `count` unique motion prompts from MOTION_POOL."""
    return random.sample(MOTION_POOL, min(count, len(MOTION_POOL)))


def _convert_gdrive_url(url: str) -> str:
    match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if match:
        return f"https://drive.google.com/uc?export=download&id={match.group(1)}"
    return url


def _run_wan22(image_url: str, prompt: str, duration: int) -> str | None:
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "input": {
            "prompt": prompt,
            "image": _convert_gdrive_url(image_url),
            "num_frames": 81 if duration <= 5 else 161,
            "aspect_ratio": "9:16",
        }
    }

    with httpx.Client(timeout=600) as client:
        res = client.post(WAN_URL, headers=headers, json=body)
        if res.status_code not in (200, 201):
            print(f"[WAN-2.2] {res.status_code}: {res.text[:300]}")
            res.raise_for_status()
        prediction = res.json()

        poll_url = prediction["urls"]["get"]
        while prediction["status"] not in ("succeeded", "failed", "canceled"):
            time.sleep(5)
            res = client.get(poll_url, headers=headers)
            res.raise_for_status()
            prediction = res.json()

        if prediction["status"] == "succeeded" and prediction.get("output"):
            output = prediction["output"]
            return output[0] if isinstance(output, list) else output

    return None


def generate_cinematic_clips(image_urls: list[str],
                             motion_prompts: list[str] | None = None,
                             duration_per_clip: int = 5) -> list[str]:
    """
    Animate each scene image into a short 9:16 clip using Wan 2.2 Fast.
    Returns list of video URLs (may be shorter than input on partial failure).
    """
    if not REPLICATE_API_TOKEN:
        print("[WAN-2.2] No REPLICATE_API_TOKEN set, skipping")
        return []

    # Auto-vary motion across clips when caller didn't specify — draws a unique
    # motion prompt per scene from MOTION_POOL (fallback = DEFAULT on exhaustion).
    if not motion_prompts:
        motion_prompts = get_varied_motion(count=len(image_urls))
        print(f"[WAN-2.2] Randomized motion prompts: {len(motion_prompts)} picked")

    clips = []
    for i, img in enumerate(image_urls):
        prompt = motion_prompts[i] if i < len(motion_prompts) else DEFAULT_MOTION_PROMPT
        if i > 0:
            time.sleep(3)
        print(f"[WAN-2.2] Animating {i + 1}/{len(image_urls)}...")
        try:
            url = _run_wan22(img, prompt, duration_per_clip)
        except Exception as e:
            print(f"[WAN-2.2] Clip {i + 1} error: {e}")
            url = None
        if url:
            clips.append(url)
            print(f"[WAN-2.2] Clip {i + 1} done")
        else:
            print(f"[WAN-2.2] Clip {i + 1} failed")

    return clips
