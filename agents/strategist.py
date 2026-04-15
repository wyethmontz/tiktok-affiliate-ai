from core.llm import call_claude

def run_strategist(input_data, insights=None):

    product = input_data["product"]
    audience = input_data.get("audience", "")
    goal = input_data.get("goal", "")

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
- The hook, angle, and positioning MUST be relevant to the target audience
- Do NOT invent prices, statistics, claims, or product details that aren't in the input
- Do NOT fabricate testimonials or fake social proof
- Use TikTok-native formats: POV, storytime, GRWM, "things I found on TikTok Shop", duet-bait, unboxing
- The angle should feel organic, not like a traditional ad
- Main goal: boost engagement, attract views, and drive clicks

IF NO AUDIENCE IS PROVIDED:
- Auto-determine the best target audience based on the product
- Think about who would actually buy this on TikTok Shop (age, gender, interests, Filipino context)

IF NO GOAL IS PROVIDED:
- Default goal: "Boost engagement, attract views, and drive affiliate clicks"

IMPORTANT: Write the hook in Tagalog (natural spoken Filipino, not formal). The angle and positioning can be in English.

EXAMPLE OUTPUT:
{{
  "hook": "POV: nahanap mo yung lip tint na hinahanap ng lahat",
  "angle": "TikTok Shop discovery storytime",
  "positioning": "hidden gem product for school fits",
  "tiktok_format": "GRWM",
  "auto_audience": "Gen Z Filipina students who love affordable beauty finds",
  "auto_goal": "Drive affiliate clicks via TikTok Shop link"
}}

{insights_block}REAL INPUT:
Product: {product}
Audience: {audience if audience else "(auto-detect from product)"}
Platform: TikTok
Goal: {goal if goal else "Boost engagement, attract views, and drive clicks"}

Return ONLY JSON with keys: hook, angle, positioning, tiktok_format, auto_audience, auto_goal.
"""

    return call_claude(prompt)
