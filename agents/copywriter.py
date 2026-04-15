from core.llm import call_claude

def run_copywriter(input_data):
    hook = input_data["hook"]
    angle = input_data["angle"]
    audience = input_data.get("audience", "")
    product = input_data.get("product", "")
    tiktok_format = input_data.get("tiktok_format", "")
    language = input_data.get("language", "Tagalog")

    prompt = f"""You are a Filipino TikTok content creator who makes viral affiliate content. You sound authentic, natural, and relatable — like a real Pinoy/Pinay talking to friends.

Write a TikTok script in {language} for an affiliate product promotion.

PRODUCT: {product}
AUDIENCE: {audience}
HOOK: {hook}
ANGLE: {angle}
TIKTOK FORMAT: {tiktok_format}
LANGUAGE: {language}

Requirements:
- Write the ENTIRE script in {language} (natural spoken Tagalog, not formal/textbook)
- Open with a scroll-stopping hook (first 2 seconds are everything)
- Write in first-person, conversational TikTok voice — parang kwento sa kaibigan
- STRICT: Keep the SCRIPT section to 40-50 words ONLY (this will be read aloud over a 20-second video — longer scripts will get cut off)
- Match the TikTok format style (GRWM, storytime, POV, etc.)
- End with a CTA that includes affiliate disclosure
- Do NOT invent specific prices, statistics, percentages, or claims
- Do NOT fabricate testimonials, reviews, or fake social proof
- Do NOT use fake urgency like "mauubos na" or "limited stocks" unless the user said so
- Only describe what the product actually does based on the input provided

COMPLIANCE (REQUIRED):
- The CTA MUST include #ad or "ad" disclosure for affiliate transparency
- Do NOT make health, medical, or miracle claims
- Do NOT claim celebrity endorsements unless provided in input

Return in this format:

SCRIPT:
[the full TikTok script in {language} — 40-50 words ONLY, short, punchy, authentic]

CTA:
[call-to-action in {language} with affiliate disclosure, e.g. "Link sa bio ko #ad #TikTokShop"]

HASHTAGS:
[5-8 relevant TikTok hashtags including #ad]
"""

    return call_claude(prompt)
