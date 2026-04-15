import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
KONTEXT_API_URL = "https://api.replicate.com/v1/models/black-forest-labs/flux-kontext-pro/predictions"

# Scene prompts: each generates a realistic "in-use" image from the product photo
TOY_SCENE_PROMPTS = [
    (
        "Close-up of a person's hands excitedly unboxing this product from a colorful package, "
        "overhead angle, bright natural lighting, TikTok vertical format, authentic phone-shot feel"
    ),
    (
        "A pair of hands holding this product up to the camera showing it off, "
        "shallow depth of field, warm soft lighting, clean background, "
        "vertical 9:16 TikTok style, casual social media photo"
    ),
    (
        "This product being used and played with on a table, hands interacting with it, "
        "close-up action shot, colorful playful background, natural lighting, "
        "vertical 9:16 TikTok content style"
    ),
    (
        "This product displayed beautifully with someone's hand reaching for it, "
        "aesthetic flat lay style, soft pastel background, vertical 9:16, "
        "TikTok product showcase angle, inviting and clickable"
    ),
]

# Generic prompts for non-toy products
GENERIC_SCENE_PROMPTS = [
    (
        "Close-up of hands unboxing this product from packaging, "
        "overhead shot, natural lighting, TikTok vertical 9:16 format"
    ),
    (
        "A person's hands holding this product up to camera, showing it off proudly, "
        "shallow depth of field, clean background, vertical 9:16 TikTok style"
    ),
    (
        "This product being used in a real-life setting, hands interacting with it, "
        "close-up shot, warm natural lighting, vertical 9:16 social media content"
    ),
    (
        "Aesthetic product shot of this item with a hand reaching into frame, "
        "soft lighting, clean background, vertical 9:16 TikTok showcase style"
    ),
]


def _run_kontext(product_image_url: str, prompt: str) -> str | None:
    """Call Flux Kontext Pro to generate a product-in-context scene."""
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "input": {
            "prompt": prompt,
            "input_image": product_image_url,
            "aspect_ratio": "9:16",
            "output_format": "webp",
            "output_quality": 80,
            "num_inference_steps": 28,
            "guidance": 2.5,
        }
    }

    with httpx.Client(timeout=120) as client:
        res = client.post(KONTEXT_API_URL, headers=headers, json=body)
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

    prompts = TOY_SCENE_PROMPTS if product_type == "toy" else GENERIC_SCENE_PROMPTS
    prompts = prompts[:num_scenes]

    scene_urls = []
    for i, prompt in enumerate(prompts):
        try:
            if i > 0:
                time.sleep(3)  # Avoid rate limiting
            print(f"[KONTEXT] Generating scene {i + 1}/{len(prompts)}...")
            url = _run_kontext(product_image_url, prompt)
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
