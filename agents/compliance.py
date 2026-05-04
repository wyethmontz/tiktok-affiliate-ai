from core.llm import call_claude

def run_compliance(input_data):
    """Check ad content for TikTok policy violations before publishing."""
    copy = input_data["copy"]
    creative = input_data.get("creative", "")
    original_input = input_data.get("original_input", "")
    latest_rules = input_data.get("latest_rules", "")

    prompt = f"""You are a TikTok advertising compliance reviewer specializing in AIGC (AI-Generated Content) policy. Your job is to check affiliate ad content for policy violations.

ORIGINAL USER INPUT (what was actually provided):
{original_input}

AD COPY:
{copy}

CREATIVE PLAN:
{creative}

Check for ALL of the following violations:

1. FABRICATED CLAIMS — Does the ad invent specific prices, statistics, percentages, or measurable product claims NOT in the original input? (e.g., "$8" when no price was given, "12-hour wear" when not specified). Note: General marketing language like "must-have", "super cute", "ganda nito" is NOT a fabricated claim — only flag specific numbers or testable claims.

2. FAKE TESTIMONIALS — Does the ad reference fake reviews, fake social proof, or fabricated endorsements? (e.g., "celebrity uses this", "makeup artists are hoarding this")

3. FAKE URGENCY — Does the ad claim "limited stock", "selling out fast", "mauubos na", or "only X left" without evidence?

4. HEALTH/MEDICAL CLAIMS — Does the ad make medical, health, or miracle claims? (e.g., "cures acne", "clinically proven")

5. MISSING AFFILIATE DISCLOSURE — Does the CTA include #ad, "ad", or affiliate disclosure?

6. MISSING AIGC DISCLOSURE — Does the hashtag section include #AIgenerated or similar AI content disclosure?

7. PUBLIC FIGURES — Does the ad reference, portray, or claim endorsement by any real public figure, celebrity, or influencer? (TikTok PROHIBITS this in AIGC even if labeled)

8. FAKE IN-HAND USAGE — Does the ad CLAIM a real person reviewed, tested, or endorsed the product when no real person was involved? Note: AI-generated images showing hands holding a product for visual demonstration are ALLOWED as long as the content is labeled as AI-generated (which our pipeline handles automatically with #AIgenerated). This is standard product visualization, not fake endorsement.

9. MISLEADING CONTENT — Does the ad misrepresent what the product does beyond what was provided? Note: Describing the product's appearance (color, design, features visible in the photo) is fine. Only flag claims about performance, quality, or results that aren't in the input.

{"" if not latest_rules else f'''
10. LATEST TIKTOK POLICY UPDATES (fetched from TikTok's official policy pages):
{latest_rules}

Check the ad against these latest rules as well. If any new rule is violated, flag it.
'''}
Return in this format:

STATUS: PASS or FAIL
ISSUES:
- [list each violation found, or "None" if compliant]
FIXES:
- [specific fix for each issue, or "None" if compliant]
AIGC REMINDER: When posting this content to TikTok, enable the "AI-generated content" toggle in Post Settings > More options.
"""

    return call_claude(prompt)
