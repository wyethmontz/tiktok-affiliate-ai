from core.llm import call_claude

def run_strategist(input_data, insights=None):

    product = input_data["product"]
    audience = input_data.get("audience", "")
    goal = input_data.get("goal", "")
    past_hooks = input_data.get("past_hooks", [])

    past_hooks_block = ""
    if past_hooks:
        hooks_list = "\n".join(f"- {h}" for h in past_hooks)
        past_hooks_block = f"""
RECENTLY USED HOOKS (do NOT repeat these or use similar patterns):
{hooks_list}

Write a hook that uses a COMPLETELY DIFFERENT style and opening from all of the above.
"""

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

HOOK VARIETY (CRITICAL):
- Each hook MUST use a DIFFERENT opening style. Rotate between these:
  * Reaction: "Grabe!" / "Wait, legit ba?"
  * Question: "Alam niyo ba...?" / "Sino dito...?"
  * Storytime: "Kinulit ako ng anak ko..."
  * Challenge: "Hanap niyo ito sa mall..."
  * Show-off: "Tignan niyo ito..."
  * Surprise: "Hindi ko inexpect na ganito kaganda..."
- Do NOT start with "Grabe ang ganda" — that pattern is overused
- Do NOT always use "POV:" format
- The hook must be in Tagalog, natural spoken Filipino

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

{insights_block}{past_hooks_block}REAL INPUT:
Product: {product}
Audience: {audience if audience else "(auto-detect from product)"}
Platform: TikTok
Goal: {goal if goal else "Boost engagement, attract views, and drive clicks"}

Return ONLY JSON with keys: hook, angle, positioning, tiktok_format, auto_audience, auto_goal.
"""

    return call_claude(prompt)
