from core.llm import call_claude

def run_qa(input_data):
    content = input_data["content"]

    prompt = f"""You are a senior ad quality evaluator at a cosmetics brand.

Score this ad content and provide actionable feedback.

AD CONTENT:
{content}

Evaluate on these criteria:
1. Hook strength (does it stop the scroll?)
2. Emotional appeal (does it create desire?)
3. Clarity (is the message instantly clear?)
4. Call-to-action (is it specific and urgent?)
5. Platform fit (would this work on social media?)

Return in this EXACT format:

Score: [number]/10

Strengths:
- [what works well]

Improvements:
- [specific, actionable changes to make it better]
"""

    return call_claude(prompt)
