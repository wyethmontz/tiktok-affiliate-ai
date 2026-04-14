from core.llm import call_claude

def run_media(input_data):
    scenes = input_data["scenes"]

    prompt = f"""You are a visual prompt engineer specializing in AI image generation with Flux for TikTok content.

Convert these TikTok ad scenes into detailed prompts for Flux AI image generation.

SCENES:
{scenes}

RULES:
- Create one prompt per scene, exactly 4 prompts
- Each prompt must be a single line (no line breaks within a prompt)
- Do NOT use markdown formatting (no bold, no asterisks, no headers)
- Do NOT prefix with "Scene 1:" or similar labels
- Each prompt should be a plain, detailed description
- ALL images must look like TikTok content — vertical framing, phone-shot feel, not stock photos
- Include "vertical 9:16 aspect ratio" in every prompt
- Style should be authentic social media content, not polished advertising

For each prompt include:
- Subject and action
- Vertical 9:16 framing (phone screen format)
- Lighting (natural, ring light, or selfie lighting — TikTok native)
- Camera style (selfie angle, phone on tripod, handheld)
- Style reference (TikTok aesthetic, iPhone photo, casual social media content)
- Color palette and mood

Return each prompt on its own line, numbered:

1. [detailed image prompt]
2. [detailed image prompt]
3. [detailed image prompt]
4. [detailed image prompt]
"""

    return call_claude(prompt)
