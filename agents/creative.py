from core.llm import call_claude

def run_creative(input_data):
    script = input_data["script"]
    tiktok_format = input_data.get("tiktok_format", "")

    prompt = f"""You are a TikTok creative director who makes viral short-form content.

Break this TikTok script into a visual scene plan.

TIKTOK FORMAT: {tiktok_format}
SCRIPT:
{script}

RULES:
- EXACTLY 4 scenes (TikTok ads must be tight — 15-30 seconds total)
- Each scene is 4-7 seconds
- All shots are vertical 9:16 (phone screen format)
- Camera style: handheld, selfie-cam, or phone-on-tripod (authentic TikTok feel)
- No overly polished/corporate looks — it should feel native to TikTok
- Match the TikTok format (GRWM = mirror shots, POV = first-person, etc.)

Return in this format:

SCENES:
Scene 1: [what the viewer sees, camera angle, action, 4-7s]
Scene 2: [what the viewer sees, camera angle, action, 4-7s]
Scene 3: [what the viewer sees, camera angle, action, 4-7s]
Scene 4: [what the viewer sees, camera angle, action, 4-7s]

VISUAL STYLE:
[aesthetic, color palette, lighting — must feel like native TikTok content]

TEXT OVERLAYS:
[what text appears on screen and when — TikTok users watch on mute]
"""

    return call_claude(prompt)
