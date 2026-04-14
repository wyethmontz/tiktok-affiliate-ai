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


def generate_images(media_prompts: str, max_images: int = 4) -> list[str]:
    """
    Takes the numbered media prompts from the media agent,
    extracts individual prompts, and generates images via Flux on Replicate.
    Returns a list of image URLs.
    """
    # Extract numbered prompts (e.g. "1. ...", "2. ...")
    lines = re.findall(r'\d+\.\s*(.+)', media_prompts)
    # Strip markdown formatting and scene labels
    lines = [re.sub(r'\*{1,2}', '', l) for l in lines]  # remove bold/italic markers
    lines = [re.sub(r'^Scene\s*\d+:?\s*', '', l, flags=re.IGNORECASE).strip() for l in lines]
    lines = [l for l in lines if l]
    if not lines:
        lines = [l.strip() for l in media_prompts.split('\n') if l.strip()]

    lines = lines[:max_images]

    image_urls = []
    for i, prompt in enumerate(lines):
        try:
            if i > 0:
                time.sleep(5)  # Avoid rate limiting between requests
            url = _run_prediction(prompt)
            if url:
                image_urls.append(url)
        except Exception as e:
            # Retry once after a longer wait on rate limit
            if "429" in str(e):
                print(f"[IMAGE GEN] Rate limited, retrying in 10s...")
                time.sleep(10)
                try:
                    url = _run_prediction(prompt)
                    if url:
                        image_urls.append(url)
                except Exception as e2:
                    print(f"[IMAGE GEN ERROR] Retry failed: {e2}")
            else:
                print(f"[IMAGE GEN ERROR] {e}")
            continue

    return image_urls
