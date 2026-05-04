import os
import re
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_API_URL = "https://api.replicate.com/v1/models/black-forest-labs/flux-schnell/predictions"


def _run_prediction(prompt: str) -> str | None:
    """Call Replicate API directly, poll until complete, return image URL."""
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "input": {
            "prompt": prompt,
            "num_outputs": 1,
            "aspect_ratio": "9:16",
            "output_format": "webp",
            "output_quality": 80,
        }
    }

    with httpx.Client(timeout=60) as client:
        # Create prediction
        res = client.post(REPLICATE_API_URL, headers=headers, json=body)
        res.raise_for_status()
        prediction = res.json()

        # Poll until done
        poll_url = prediction["urls"]["get"]
        while prediction["status"] not in ("succeeded", "failed", "canceled"):
            time.sleep(1)
            res = client.get(poll_url, headers=headers)
            res.raise_for_status()
            prediction = res.json()

        if prediction["status"] == "succeeded" and prediction.get("output"):
            return prediction["output"][0]

    return None


PRODUCT_PHOTO_MARKER = "PRODUCT_PHOTO"


def generate_images(media_prompts: str, max_images: int = 4) -> list[str | None]:
    """
    Takes the numbered media prompts from the media agent,
    extracts individual prompts, and generates images via Flux on Replicate.
    PRODUCT_PHOTO lines are returned as None (to be filled with real product images later).
    Returns a list of image URLs (or None for product photo slots).
    """
    # Extract numbered prompts (e.g. "1. ...", "2. ...")
    lines = re.findall(r'\d+\.\s*(.+)', media_prompts)
    # Strip markdown formatting and scene labels
    lines = [re.sub(r'\*{1,2}', '', line) for line in lines]
    lines = [re.sub(r'^Scene\s*\d+:?\s*', '', line, flags=re.IGNORECASE).strip() for line in lines]
    lines = [line for line in lines if line]
    if not lines:
        lines = [line.strip() for line in media_prompts.split('\n') if line.strip()]

    lines = lines[:max_images]

    image_urls = []
    for i, prompt in enumerate(lines):
        # Skip product photo slots — will be filled with real images
        if PRODUCT_PHOTO_MARKER in prompt.upper():
            image_urls.append(None)
            print(f"[IMAGE GEN] Scene {i + 1}: product photo slot (skipped)")
            continue

        try:
            if i > 0 and image_urls and image_urls[-1] is not None:
                time.sleep(5)  # Avoid rate limiting between requests
            print(f"[IMAGE GEN] Scene {i + 1}: generating AI image...")
            url = _run_prediction(prompt)
            if url:
                image_urls.append(url)
            else:
                image_urls.append(None)
        except Exception as e:
            # Retry once after a longer wait on rate limit
            if "429" in str(e):
                print("[IMAGE GEN] Rate limited, retrying in 10s...")
                time.sleep(10)
                try:
                    url = _run_prediction(prompt)
                    if url:
                        image_urls.append(url)
                    else:
                        image_urls.append(None)
                except Exception as e2:
                    print(f"[IMAGE GEN ERROR] Retry failed: {e2}")
                    image_urls.append(None)
            else:
                print(f"[IMAGE GEN ERROR] {e}")
                image_urls.append(None)

    return image_urls
