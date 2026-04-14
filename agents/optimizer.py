"""Optimizer agent: analyzes top-performing ads and generates insights
for the strategist to use in future ad generation."""
import re
from core.db import supabase
from core.llm import call_claude


def get_top_ads(limit=10):
    """Fetch the top-scoring ads from the database."""
    ads = supabase.table("ads").select("*").order("created_at", desc=True).limit(50).execute().data

    scored = []
    for ad in ads:
        score = ad.get("qa_score_numeric")
        if score is None:
            match = re.search(r"\d+", ad.get("qa_score", "") or "")
            score = int(match.group()) if match else 0
        scored.append({**ad, "_score": score})

    scored.sort(key=lambda a: a["_score"], reverse=True)
    return scored[:limit]


def run_optimizer():
    """Analyze top ads and return strategic insights for the strategist."""
    top_ads = get_top_ads()

    if len(top_ads) < 3:
        return None  # Not enough data to generate insights

    ads_summary = "\n".join(
        f"- Product: {a.get('product')}, Hook: {a.get('hook')}, "
        f"Angle: {a.get('angle')}, Score: {a['_score']}/10"
        for a in top_ads
    )

    prompt = f"""You are an advertising analytics expert.

Analyze these top-performing ads and extract 3-5 key insights about what makes them work.
Focus on: hook patterns, angle strategies, and positioning that scores highest.

TOP ADS:
{ads_summary}

Return a brief paragraph of actionable insights that a marketing strategist can use
to create better ads. Be specific about patterns you see.
"""

    return call_claude(prompt)
