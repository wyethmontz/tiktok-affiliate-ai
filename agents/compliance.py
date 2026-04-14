from core.llm import call_claude

def run_compliance(input_data):
    """Check ad content for TikTok policy violations before publishing."""
    copy = input_data["copy"]
    creative = input_data.get("creative", "")
    product = input_data.get("product", "")
    original_input = input_data.get("original_input", "")

    prompt = f"""You are a TikTok advertising compliance reviewer specializing in AIGC (AI-Generated Content) policy. Your job is to check affiliate ad content for policy violations.

ORIGINAL USER INPUT (what was actually provided):
{original_input}

AD COPY:
{copy}

CREATIVE PLAN:
{creative}

Check for ALL of the following violations:

1. FABRICATED CLAIMS — Does the ad invent prices, statistics, percentages, or product details NOT in the original input? (e.g., "$8" when no price was given, "12-hour wear" when not specified)

2. FAKE TESTIMONIALS — Does the ad reference fake reviews, fake social proof, or fabricated endorsements? (e.g., "celebrity uses this", "makeup artists are hoarding this")

3. FAKE URGENCY — Does the ad claim "limited stock", "selling out fast", "mauubos na", or "only X left" without evidence?

4. HEALTH/MEDICAL CLAIMS — Does the ad make medical, health, or miracle claims? (e.g., "cures acne", "clinically proven")

5. MISSING AFFILIATE DISCLOSURE — Does the CTA include #ad, "ad", or affiliate disclosure?

6. MISSING AIGC DISCLOSURE — Does the hashtag section include #AIgenerated or similar AI content disclosure?

7. PUBLIC FIGURES — Does the ad reference, portray, or claim endorsement by any real public figure, celebrity, or influencer? (TikTok PROHIBITS this in AIGC even if labeled)

8. FAKE IN-HAND USAGE — Does the creative plan describe scenes where an AI-generated person appears to hold, use, or demonstrate the product as if they are a real person? (This is misleading AIGC)

9. MISLEADING CONTENT — Does the ad misrepresent what the product does beyond what was provided?

Return in this format:

STATUS: PASS or FAIL
ISSUES:
- [list each violation found, or "None" if compliant]
FIXES:
- [specific fix for each issue, or "None" if compliant]
AIGC REMINDER: When posting this content to TikTok, enable the "AI-generated content" toggle in Post Settings > More options.
"""

    return call_claude(prompt)
