from core.llm import call_claude

def run_strategist(input_data, insights=None):

    product = input_data["product"]
    audience = input_data["audience"]
    goal = input_data["goal"]

    insights_block = ""
    if insights:
        insights_block = f"""
INSIGHTS FROM PAST HIGH-PERFORMING ADS:
{insights}

Use these insights to inform your strategy.

"""

    prompt = f"""
You are a TikTok affiliate marketing strategist. You specialize in creating viral TikTok Shop content that converts.

Return ONLY valid JSON.

RULES:
- This is for TikTok affiliate marketing — the hook must stop the scroll in under 2 seconds
- The hook, angle, and positioning MUST be relevant to the specific audience
- Do NOT invent prices, statistics, claims, or product details that aren't in the input
- Do NOT fabricate testimonials or fake social proof
- Stay true to the audience description — match their lifestyle, language, and interests
- Use TikTok-native formats: POV, storytime, GRWM, "things I found on TikTok Shop", duet-bait, unboxing
- The angle should feel organic, not like a traditional ad

EXAMPLE OUTPUT:
{{
  "hook": "POV: you find the lip tint everyone's been hiding",
  "angle": "TikTok Shop discovery storytime",
  "positioning": "hidden gem product for school fits",
  "tiktok_format": "GRWM"
}}

{insights_block}REAL INPUT:
Product: {product}
Audience: {audience}
Platform: TikTok
Goal: {goal}

Return ONLY JSON with keys: hook, angle, positioning, tiktok_format.
"""

    return call_claude(prompt)
