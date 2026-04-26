"""
Cinematic scenes generator — nano-banana (Replicate).
Cheaper + more aesthetic alternative to Flux Kontext Pro.
Used by the DISCOVERY (no-basket) pipeline path. ~$0.04 per scene.
"""
import os
import re
import base64
import time
import random
import httpx
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
NANO_BANANA_URL = "https://api.replicate.com/v1/models/google/nano-banana/predictions"

# Product-type-aware scene buckets. Each entry is a short setting descriptor;
# FRAME_SUFFIX adds the TikTok-format framing rules at build time.
# 6 scenes × 4 picks → C(6,4)=15 combinations per bucket, so 60 Discovery videos
# over a 30-day campaign will effectively never repeat within a product category.
SCENE_BUCKETS = {
    "die-cast": [
        "on a mahogany desk with warm lamp lighting",
        "displayed on a minimalist glass shelf",
        "in a macro shot on a custom car display case",
        "sitting on a realistic asphalt-texture diorama",
        "positioned next to a collection of other luxury car models",
        "low-angle heroic shot on a clean white surface",
    ],
    "action-figure": [
        "inside a collector's glass display cabinet, soft volumetric backlight, shallow depth of field",
        "posed on a shelf with comic books in the background, warm rim lighting, cinematic bokeh",
        "macro shot focused on high-detail paint and accessories, shallow depth of field with bokeh",
        "dynamic low-angle hero pose on a gaming setup desk, subtle atmospheric haze, dramatic key light",
        "unboxing style: sitting inside a pristine open box, soft natural daylight, gentle highlights",
        "dramatic side lighting on a dark textured surface, cinematic god-rays from above, anime-edit aesthetic",
    ],
    "plushie": [
        "nestled in a cozy aesthetic bedroom setup",
        "sitting on a soft white cloud-like rug",
        "surrounded by fairy lights and soft pastel pillows",
        "displayed on a cute wooden bookshelf",
        "next to a cup of coffee and an open journal",
        "close-up shot on a soft knitted blanket",
    ],
    "building-blocks": [
        "on a bright workbench with scattered loose bricks around, specular highlights on smooth ABS plastic surfaces, matte texture detail",
        "displayed as a centerpiece on a modern living room shelf, realistic plastic material with subtle gloss reflections",
        "partially built with a focus on the structural complexity, sharp specular highlights on plastic edges",
        "under bright studio lighting on a plain neutral-gray platform, matte ABS plastic finish with realistic material reflections",
        "macro shot of the small figures positioned in a scene, glossy plastic surfaces with realistic light bounce, fine surface detail",
        "on a playmat with other structures in the background, accurate plastic material rendering with subtle highlights",
    ],
    # Fallback for products that don't fit the 4 main buckets
    # (beyblades, drones, foam blasters, baby toys, kitchen sets, etc.)
    "generic": [
        "on a clean white marble surface with soft natural lighting",
        "centered in a minimalist display with pastel backdrop",
        "on a wooden desk next to scattered craft supplies",
        "on a soft fabric backdrop with warm afternoon light",
        "displayed on a modern geometric shelf with plants nearby",
        "on a clean studio background with gentle rim lighting",
    ],
}

# Framing rules appended to every scene descriptor so nano-banana produces
# TikTok-ready output regardless of which bucket was picked.
# Strict anti-branding suffix: nano-banana will otherwise hallucinate store
# signage, brand logos, and promotional text when prompts contain store
# references or adjectives like "retail" / "store" — causing trademark risk.
FRAME_SUFFIX = (
    "9:16 vertical TikTok format, only one product visible, no duplicates, "
    "phone-shot authentic feel, sharp focus on the product, "
    "NO text in image, NO logos, NO brand names, NO store signage, "
    "NO promotional banners, NO price tags, NO watermarks, "
    "background is plain and clean without any readable text"
)


def get_varied_scenes(product_type: str = "generic", count: int = 4) -> list[str]:
    """Draw `count` unique scene prompts from the product_type bucket.
    Falls back to 'generic' for unknown product types (safer than die-cast
    which renders car-showroom visuals on baby toys / kitchen sets / etc)."""
    pool = SCENE_BUCKETS.get(product_type, SCENE_BUCKETS["generic"])
    contexts = random.sample(pool, min(count, len(pool)))
    return [f"this product {ctx}, {FRAME_SUFFIX}" for ctx in contexts]


def _convert_gdrive_url(url: str) -> str:
    match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if match:
        return f"https://drive.google.com/uc?export=download&id={match.group(1)}"
    return url


def _url_to_data_uri(url: str) -> str:
    if url.startswith("data:"):
        return url
    url = _convert_gdrive_url(url)
    print(f"[NANO-BANANA] Downloading image: {url[:80]}...")
    with httpx.Client(timeout=30, follow_redirects=True) as client:
        res = client.get(url)
        res.raise_for_status()
        content_type = res.headers.get("content-type", "image/jpeg").split(";")[0]
        b64 = base64.b64encode(res.content).decode()
        return f"data:{content_type};base64,{b64}"


def _run_nano_banana(image_data_uri: str, prompt: str) -> str | None:
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    body = {
        "input": {
            "prompt": prompt,
            "image_input": [image_data_uri],
            "output_format": "jpg",
        }
    }

    with httpx.Client(timeout=180) as client:
        res = client.post(NANO_BANANA_URL, headers=headers, json=body)
        if res.status_code not in (200, 201):
            print(f"[NANO-BANANA] {res.status_code}: {res.text[:300]}")
            res.raise_for_status()
        prediction = res.json()

        poll_url = prediction["urls"]["get"]
        while prediction["status"] not in ("succeeded", "failed", "canceled"):
            time.sleep(2)
            res = client.get(poll_url, headers=headers)
            res.raise_for_status()
            prediction = res.json()

        if prediction["status"] == "succeeded" and prediction.get("output"):
            output = prediction["output"]
            return output[0] if isinstance(output, list) else output

    return None


def generate_cinematic_scenes(product_image_url: str, num_scenes: int = 4,
                              prompts: list[str] | None = None,
                              product_type: str = "die-cast") -> list[str]:
    """
    Takes a single product photo and generates `num_scenes` cinematic / lifestyle
    scenes using Google's nano-banana on Replicate. Scene prompts are drawn from
    the matching SCENE_BUCKETS entry (randomized per run for 30-day variety).

    Returns list of image URLs (may be shorter than num_scenes on partial failure).
    """
    if not REPLICATE_API_TOKEN:
        print("[NANO-BANANA] No REPLICATE_API_TOKEN set, skipping")
        return []

    try:
        image_data_uri = _url_to_data_uri(product_image_url)
        print(f"[NANO-BANANA] Product image loaded ({len(image_data_uri) // 1024}KB)")
    except Exception as e:
        print(f"[NANO-BANANA] Failed to download product image: {e}")
        return []

    if prompts is None:
        prompts = get_varied_scenes(product_type=product_type, count=num_scenes)
        print(f"[NANO-BANANA] Using '{product_type}' bucket ({len(prompts)} scenes picked)")
    else:
        prompts = prompts[:num_scenes]

    urls = []
    for i, prompt in enumerate(prompts):
        if i > 0:
            time.sleep(2)
        print(f"[NANO-BANANA] Scene {i + 1}/{len(prompts)}...")
        try:
            url = _run_nano_banana(image_data_uri, prompt)
        except Exception as e:
            print(f"[NANO-BANANA] Scene {i + 1} error: {e}")
            url = None
        if url:
            urls.append(url)
            print(f"[NANO-BANANA] Scene {i + 1} done")
        else:
            print(f"[NANO-BANANA] Scene {i + 1} failed")

    return urls
