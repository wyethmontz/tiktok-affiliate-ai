from core.llm import call_claude

def run_creative(input_data):
    script = input_data["script"]
    tiktok_format = input_data.get("tiktok_format", "")
    has_product_images = input_data.get("has_product_images", False)

    if has_product_images:
        scene_layout = """- EXACTLY 4 scenes in this order:
  - Scene 1 [AI]: Lifestyle/hook scene — grab attention, NO product yet (AI-generated)
  - Scene 2 [PRODUCT]: Real product closeup — this uses the actual product photo
  - Scene 3 [AI]: Product in use context — show the benefit/result (AI-generated)
  - Scene 4 [PRODUCT]: Product beauty shot + CTA — this uses the actual product photo
- Tag each scene with [AI] or [PRODUCT] at the start"""
    else:
        scene_layout = """- EXACTLY 4 scenes (all AI-generated)
- Each scene should visually tell the product story"""

    prompt = f"""You are a TikTok creative director who makes viral short-form affiliate content that drives sales.

Break this TikTok script into a visual scene plan.

TIKTOK FORMAT: {tiktok_format}
SCRIPT:
{script}

RULES:
{scene_layout}
- Each scene is 4-7 seconds
- All shots are vertical 9:16 (phone screen format)
- Camera style: handheld, selfie-cam, or phone-on-tripod (authentic TikTok feel)
- No overly polished/corporate looks — it should feel native to TikTok
- Match the TikTok format (GRWM = mirror shots, POV = first-person, etc.)
- [PRODUCT] scenes should describe how to frame/present the product photo (angle, background, zoom level)
- [AI] scenes should create desire and context around the product

Return in this format:

SCENES:
Scene 1 [AI]: [what the viewer sees, camera angle, action, 4-7s]
Scene 2 [PRODUCT]: [how to present the product photo, framing, 4-7s]
Scene 3 [AI]: [what the viewer sees, camera angle, action, 4-7s]
Scene 4 [PRODUCT]: [product beauty shot framing + CTA overlay, 4-7s]

VISUAL STYLE:
[aesthetic, color palette, lighting — must feel like native TikTok content]

TEXT OVERLAYS:
[what text appears on screen and when — TikTok users watch on mute]
"""

    return call_claude(prompt)
