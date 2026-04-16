from core.llm import call_claude

def run_copywriter(input_data):
    hook = input_data["hook"]
    angle = input_data["angle"]
    audience = input_data.get("audience", "")
    product = input_data.get("product", "")
    tiktok_format = input_data.get("tiktok_format", "")
    language = input_data.get("language", "Tagalog")
    past_hooks = input_data.get("past_hooks", [])

    dedup_block = ""
    if past_hooks:
        hooks_list = "\n".join(f"- {h}" for h in past_hooks)
        dedup_block = f"""
IMPORTANT — These hooks were already used for this product. Write something COMPLETELY DIFFERENT:
{hooks_list}

Do NOT reuse the same opening line, angle, or structure as any of the above.
"""

    prompt = f"""You are a Filipino TikTok content creator who makes viral affiliate content. You sound authentic, natural, and relatable — like a real Pinoy/Pinay talking to friends.

Write a TikTok script in {language} for an affiliate product promotion.
{dedup_block}
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
- STRICT: Keep the SCRIPT section to 30-40 words MAXIMUM (this will be read aloud over a 14-second video). Count your words before returning.
- Match the TikTok format style (GRWM, storytime, POV, etc.)
- End with a CTA that includes affiliate disclosure
- Do NOT invent specific prices or fake claims
- Do NOT fabricate testimonials, reviews, or fake social proof
- Do NOT use fake urgency like "mauubos na" or "limited stocks" unless the user said so
- Only describe what the product actually does based on the input provided
- Do NOT mention specific store names (Toy Kingdom, SM, etc.) — keep it general
- Do NOT read product specs like a listing (no "1:36 scale alloy model") — describe it naturally like a person would
- Do NOT use apostrophe contractions like 'to, 'yan, 'yung, 'di — write full words: ito, iyan, iyong, hindi (crucial for ElevenLabs voiceover)

HOOK VARIETY (CRITICAL — use a DIFFERENT style each time):
- Reaction: "Grabe ang ganda nito!" / "Wait, legit ba ito?!"
- Question: "Alam niyo ba yung toy na trending ngayon?"
- Storytime: "Anak ko kinulit ako para dito..."
- Discovery: "Guys check niyo ito!"
- Challenge: "Hanap kayo nito sa mall, wala!"
- Show-off: "Tignan niyo yung details ng toy na ito..."
Do NOT always use "POV:" or "Naghahanap ka" — pick a different style each time.

COMPLIANCE (REQUIRED):
- The CTA MUST include #ad disclosure
- Do NOT say "link sa bio" or "link in bio" — there is no link yet
- Use comment-based CTAs like: "Comment INFO kung gusto niyo rin ito! #ad" or "Comment TOY para ma-send ko link! #ad"
- Do NOT make health, medical, or miracle claims
- Do NOT claim celebrity endorsements unless provided in input

Return in this format:

SCRIPT:
[the full TikTok script in {language} — 30-40 words MAX, short, punchy]

CTA:
[comment-based CTA with #ad — e.g. "Comment INFO kung gusto niyo rin ito! #ad"]

ENGAGEMENT QUESTION:
[a "this or that" question to drive comments — e.g. "Pula o asul, alin mas mabilis? 👇" or "Pang regalo o pang collection? 😂"]

HASHTAGS:
[5-8 relevant tags including #ad #ToysPH #DiecastPH #BudolFinds #GiftIdeasPH]
"""

    return call_claude(prompt)
