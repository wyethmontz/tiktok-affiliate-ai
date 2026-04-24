import os
import re
import base64
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
KONTEXT_API_URL = "https://api.replicate.com/v1/models/black-forest-labs/flux-kontext-pro/predictions"

# Anti-branding guard: Kontext (like nano-banana) can hallucinate store signage,
# logos, and "NEW ARRIVAL" banners when exposed to retail-adjacent language.
# Append to every prompt to prevent trademark risk + commerce-signal leakage.
_NO_TEXT_GUARD = (
    "NO text in image, NO logos, NO brand names, NO store signage, "
    "NO promotional banners, NO price tags, NO watermarks"
)

# Scene prompts: each generates a realistic "in-use" image from the product photo
TOY_SCENE_PROMPTS = [
    (
        "Place this single product on a clean table, one hand reaching to pick it up, "
        "overhead angle, bright natural lighting, only one copy of the product visible, "
        f"TikTok vertical 9:16 format, authentic phone-shot feel, {_NO_TEXT_GUARD}"
    ),
    (
        "One pair of hands holding up this single product to the camera, showing it off, "
        "shallow depth of field, warm soft lighting, simple clean background, "
        f"only one product in frame, vertical 9:16 TikTok style, {_NO_TEXT_GUARD}"
    ),
    (
        "Close-up of this single product sitting on a white surface, one hand touching it, "
        "product photography style, soft even lighting, no duplicates, "
        f"vertical 9:16 TikTok content, sharp focus on the product, {_NO_TEXT_GUARD}"
    ),
    (
        "This single product centered in frame on a soft pastel background, "
        "one hand gently presenting it from the side, aesthetic flat lay, "
        f"only one product visible, vertical 9:16 TikTok showcase style, {_NO_TEXT_GUARD}"
    ),
]

# Generic prompts for non-toy products
GENERIC_SCENE_PROMPTS = [
    (
        "Close-up of hands unboxing this product from packaging, "
        f"overhead shot, natural lighting, TikTok vertical 9:16 format, {_NO_TEXT_GUARD}"
    ),
    (
        "A person's hands holding this product up to camera, showing it off proudly, "
        f"shallow depth of field, clean background, vertical 9:16 TikTok style, {_NO_TEXT_GUARD}"
    ),
    (
        "This product being used in a real-life setting, hands interacting with it, "
        f"close-up shot, warm natural lighting, vertical 9:16 social media content, {_NO_TEXT_GUARD}"
    ),
    (
        "Aesthetic product shot of this item with a hand reaching into frame, "
        f"soft lighting, clean background, vertical 9:16 TikTok showcase style, {_NO_TEXT_GUARD}"
    ),
]


def _convert_gdrive_url(url: str) -> str:
    """Convert Google Drive share links to direct download URLs."""
    match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if match:
        return f"https://drive.google.com/uc?export=download&id={match.group(1)}"
    return url


def _url_to_data_uri(url: str) -> str:
    """Download an image URL and convert to base64 data URI.
    Replicate needs a publicly accessible URL or data URI.
    Google Drive and localhost URLs don't work directly."""
    if url.startswith("data:"):
        return url

    url = _convert_gdrive_url(url)
    print(f"[KONTEXT] Downloading image: {url[:80]}...")

    with httpx.Client(timeout=30, follow_redirects=True) as client:
        res = client.get(url)
        res.raise_for_status()

        content_type = res.headers.get("content-type", "image/jpeg").split(";")[0]
        b64 = base64.b64encode(res.content).decode()
        return f"data:{content_type};base64,{b64}"


def _run_kontext(image_data_uri: str, prompt: str) -> str | None:
    """Call Flux Kontext Pro to generate a product-in-context scene."""
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "input": {
            "prompt": prompt,
            "input_image": image_data_uri,
            "aspect_ratio": "9:16",
            "output_format": "jpg",
            "output_quality": 90,
            "num_inference_steps": 30,
            "guidance": 4.0,
        }
    }

    with httpx.Client(timeout=120) as client:
        res = client.post(KONTEXT_API_URL, headers=headers, json=body)
        if res.status_code != 201 and res.status_code != 200:
            print(f"[KONTEXT] API error {res.status_code}: {res.text[:300]}")
            res.raise_for_status()
        prediction = res.json()

        poll_url = prediction["urls"]["get"]
        while prediction["status"] not in ("succeeded", "failed", "canceled"):
            time.sleep(3)
            res = client.get(poll_url, headers=headers)
            res.raise_for_status()
            prediction = res.json()

        if prediction["status"] == "succeeded" and prediction.get("output"):
            output = prediction["output"]
            if isinstance(output, list):
                return output[0]
            return output

    return None


def generate_product_scenes(product_image_url: str, num_scenes: int = 4,
                            product_type: str = "toy") -> list[str]:
    """
    Takes a single product photo and generates realistic in-use scenes
    using Flux Kontext Pro. The actual product is preserved in every output.
    Returns a list of image URLs.
    """
    if not REPLICATE_API_TOKEN:
        print("[KONTEXT] No REPLICATE_API_TOKEN set, skipping")
        return []

    # Download product image once and convert to data URI
    try:
        image_data_uri = _url_to_data_uri(product_image_url)
        print(f"[KONTEXT] Product image loaded ({len(image_data_uri) // 1024}KB data URI)")
    except Exception as e:
        print(f"[KONTEXT] Failed to download product image: {e}")
        return []

    prompts = TOY_SCENE_PROMPTS if product_type == "toy" else GENERIC_SCENE_PROMPTS
    prompts = prompts[:num_scenes]

    scene_urls = []
    for i, prompt in enumerate(prompts):
        try:
            if i > 0:
                time.sleep(3)  # Avoid rate limiting
            print(f"[KONTEXT] Generating scene {i + 1}/{len(prompts)}...")
            url = _run_kontext(image_data_uri, prompt)
            if url:
                scene_urls.append(url)
                print(f"[KONTEXT] Scene {i + 1} done")
            else:
                print(f"[KONTEXT] Scene {i + 1} failed — no output")
        except Exception as e:
            if "429" in str(e):
                print(f"[KONTEXT] Rate limited, retrying in 10s...")
                time.sleep(10)
                try:
                    url = _run_kontext(product_image_url, prompt)
                    if url:
                        scene_urls.append(url)
                except Exception as e2:
                    print(f"[KONTEXT ERROR] Retry failed: {e2}")
            else:
                print(f"[KONTEXT ERROR] {e}")

    return scene_urls
