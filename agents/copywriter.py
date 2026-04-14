from core.llm import call_claude

def run_copywriter(input_data):
    hook = input_data["hook"]
    angle = input_data["angle"]
    audience = input_data.get("audience", "")
    product = input_data.get("product", "")
    tiktok_format = input_data.get("tiktok_format", "")

    prompt = f"""You are a TikTok content creator who makes viral affiliate content. You sound authentic, not like an ad agency.

Write a TikTok script for an affiliate product promotion.

PRODUCT: {product}
AUDIENCE: {audience}
HOOK: {hook}
ANGLE: {angle}
TIKTOK FORMAT: {tiktok_format}

Requirements:
- Open with a scroll-stopping hook (first 2 seconds are everything)
- Write in first-person, conversational TikTok voice — like talking to a friend
- Keep it 60-100 words MAX (TikTok is 15-30 seconds)
- Match the TikTok format style (GRWM, storytime, POV, etc.)
- End with a CTA that includes affiliate disclosure
- Do NOT invent specific prices, statistics, percentages, or claims
- Do NOT fabricate testimonials, reviews, or fake social proof
- Do NOT use fake urgency like "selling out fast" or "limited stock" unless the user said so
- Only describe what the product actually does based on the input provided

COMPLIANCE (REQUIRED):
- The CTA MUST include #ad or "ad" disclosure for affiliate transparency
- Do NOT make health, medical, or miracle claims
- Do NOT claim celebrity endorsements unless provided in input

Return in this format:

SCRIPT:
[the full TikTok script — short, punchy, authentic]

CTA:
[call-to-action with affiliate disclosure, e.g. "Link in bio #ad #TikTokShop"]

HASHTAGS:
[5-8 relevant TikTok hashtags including #ad]
"""

    return call_claude(prompt)
