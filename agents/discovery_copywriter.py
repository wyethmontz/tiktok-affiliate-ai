from core.llm import call_claude


def run_discovery_copywriter(input_data):
    """
    Caption-only generator for NON-BASKET discovery posts.
    No #ad, no basket CTA, no affiliate disclosure. Pure engagement-style
    caption meant to ride the general FYP algorithm (not the commerce one).
    """
    product = input_data.get("product", "")
    audience = input_data.get("audience", "")
    hook = input_data.get("hook", "")
    angle = input_data.get("angle", "")
    language = input_data.get("language", "Tagalog")
    past_hooks = input_data.get("past_hooks", [])

    dedup_block = ""
    if past_hooks:
        hooks_list = "\n".join(f"- {h}" for h in past_hooks)
        dedup_block = f"""
IMPORTANT — These opening lines were already used recently. Pick a DIFFERENT style:
{hooks_list}
"""

    prompt = f"""You are a Filipino TikTok creator writing a DISCOVERY post caption.

This is NOT an affiliate post. There is NO product link, NO basket, NO #ad disclosure.
Goal: maximize FYP reach and engagement, build account authority.
{dedup_block}
PRODUCT: {product}
AUDIENCE: {audience}
HOOK IDEA: {hook}
ANGLE: {angle}
LANGUAGE: {language}

CAPTION RULES (STRICT):
- NEVER include "#ad", "#sponsored", "#affiliate", "basket", "link", "tap", "shop", "buy"
- NEVER mention prices, discounts, or sales
- NEVER invent claims, stats, or testimonials
- Do NOT use apostrophe contractions ('to, 'yan, 'yung, 'di) — write full words: ito, iyan, iyong, hindi
- Keep it natural, conversational Tagalog (parang kwento sa kaibigan)
- Open with a question, reaction, or observation — something that drives comments
- 1-3 sentences MAX. Short beats long on TikTok.
- End with an engagement question that isn't salesy

HASHTAG RULES:
- 4-6 hashtags total
- Include #AIgenerated (visuals are AI-generated)
- Include 1-2 category-specific tags (e.g. #AnimePH, #DiecastPH, #PlushiePH, #BuildingBlocks, #FidgetToys)
- Include #ToysPH or #BudolFinds for general discoverability
- NO #ad, NO #sponsored, NO #TikTokShopPH (those route to commerce algorithm)

Return EXACTLY in this format:

CAPTION:
[1-3 sentence discovery caption in {language} ending with an engagement question]

HASHTAGS:
[4-6 space-separated hashtags including #AIgenerated, NO #ad, NO #sponsored]
"""

    return call_claude(prompt)
