"""Analytics queries for the ads table."""
import re
from core.db import supabase


def get_summary():
    """Return summary stats: total ads, average score, top hooks."""
    ads = supabase.table("ads").select("*").execute().data

    total = len(ads)
    if total == 0:
        return {
            "total_ads": 0,
            "avg_score": 0,
            "top_hooks": [],
            "ads_by_platform": {},
            "score_distribution": {"low": 0, "mid": 0, "high": 0, "excellent": 0},
        }

    # Parse numeric scores
    scores = []
    scored_ads = []
    for ad in ads:
        score = ad.get("qa_score_numeric")
        if score is None:
            match = re.search(r"\d+", ad.get("qa_score", "") or "")
            score = int(match.group()) if match else None
        if score is not None:
            scores.append(score)
            scored_ads.append({**ad, "_score": score})

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    # Top 5 hooks by score
    scored_ads.sort(key=lambda a: a["_score"], reverse=True)
    top_hooks = [
        {"hook": a.get("hook", ""), "product": a.get("product", ""), "score": a["_score"]}
        for a in scored_ads[:5]
    ]

    # Ads by platform
    platforms: dict[str, int] = {}
    for ad in ads:
        p = ad.get("platform") or "Unknown"
        platforms[p] = platforms.get(p, 0) + 1

    # Score distribution
    dist = {"low": 0, "mid": 0, "high": 0, "excellent": 0}
    for s in scores:
        if s <= 3:
            dist["low"] += 1
        elif s <= 6:
            dist["mid"] += 1
        elif s <= 8:
            dist["high"] += 1
        else:
            dist["excellent"] += 1

    return {
        "total_ads": total,
        "avg_score": avg_score,
        "top_hooks": top_hooks,
        "ads_by_platform": platforms,
        "score_distribution": dist,
    }
