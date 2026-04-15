from core.llm import call_claude

def run_qa(input_data):
    content = input_data["content"]

    prompt = f"""You are a TikTok affiliate content quality evaluator.

Score this TikTok ad content and provide actionable feedback.

AD CONTENT:
{content}

Evaluate on these criteria:
1. Hook strength (does it stop the scroll in 2 seconds?)
2. Emotional appeal (does it create desire to buy?)
3. Clarity (is the message instantly clear?)
4. Call-to-action (does it drive clicks?)
5. TikTok fit (does it feel native to TikTok, not like a traditional ad?)

IMPORTANT — your suggestions must be TikTok-compliant:
- Do NOT suggest fake urgency ("only X left", "selling out")
- Do NOT suggest fabricated claims or fake social proof
- Do NOT suggest adding features/specs not mentioned in the content
- Focus on tone, pacing, hook strength, and authenticity

Return in this EXACT format:

Score: [number]/10

Strengths:
- [what works well]

Improvements:
- [specific, actionable, COMPLIANT changes]
"""

    return call_claude(prompt)
