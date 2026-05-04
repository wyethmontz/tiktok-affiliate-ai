import os
import json
import time
import httpx
from core.llm import call_claude

POLICY_CACHE_FILE = os.path.join(os.path.dirname(__file__), "..", "policy_cache.json")
CACHE_TTL = 86400  # 24 hours in seconds

# TikTok policy pages to check
TIKTOK_POLICY_URLS = [
    "https://www.tiktok.com/community-guidelines/en/ai-generated-content",
    "https://www.tiktok.com/community-guidelines/en/advertising",
    "https://ads.tiktok.com/help/article/tiktok-advertising-policies-ad-creatives-landing-page",
]


def _load_cache() -> dict | None:
    """Load cached policy rules if still fresh."""
    try:
        if os.path.exists(POLICY_CACHE_FILE):
            with open(POLICY_CACHE_FILE, "r") as f:
                cache = json.load(f)
            if time.time() - cache.get("timestamp", 0) < CACHE_TTL:
                print("[POLICY] Using cached rules (less than 24h old)")
                return cache
    except Exception:
        pass
    return None


def _save_cache(rules: str, raw_content: str):
    """Save policy rules to cache with timestamp."""
    try:
        with open(POLICY_CACHE_FILE, "w") as f:
            json.dump({
                "timestamp": time.time(),
                "rules": rules,
                "raw_length": len(raw_content),
            }, f)
    except Exception as e:
        print(f"[POLICY] Could not save cache: {e}")


def _fetch_page(url: str) -> str:
    """Fetch a web page and return its text content."""
    try:
        with httpx.Client(timeout=15, follow_redirects=True) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; TikTokPolicyChecker/1.0)"
            }
            res = client.get(url, headers=headers)
            if res.status_code == 200:
                return res.text[:10000]  # limit to 10k chars per page
    except Exception as e:
        print(f"[POLICY] Could not fetch {url}: {e}")
    return ""


def _extract_rules(raw_content: str) -> str:
    """Use Claude to extract actionable rules from raw policy page content."""
    prompt = f"""You are a TikTok policy analyst. Extract the key advertising and AIGC (AI-generated content) rules from this TikTok policy page content.

RAW CONTENT:
{raw_content[:15000]}

Return a concise bullet-point list of ONLY the rules that apply to:
1. AI-generated content (AIGC) — labeling, restrictions, prohibited content
2. Affiliate/advertising content — disclosure requirements, prohibited claims
3. Content restrictions — what gets removed or banned

Format as a simple numbered list. Be specific and actionable. Skip general platform rules that don't apply to AI affiliate content.
If the content doesn't contain relevant policy information, return "No relevant policy updates found."
"""
    return call_claude(prompt)


def get_latest_rules() -> str | None:
    """Fetch latest TikTok policy rules. Uses 24h cache to avoid repeated fetches.
    Returns a string of rules to pass to the compliance agent, or None if fetch fails."""

    # Check cache first
    cache = _load_cache()
    if cache:
        return cache.get("rules")

    # Fetch fresh policy pages
    print("[POLICY] Fetching latest TikTok policy rules...")
    raw_content = ""
    for url in TIKTOK_POLICY_URLS:
        page = _fetch_page(url)
        if page:
            raw_content += f"\n--- Source: {url} ---\n{page}\n"

    if not raw_content.strip():
        print("[POLICY] Could not fetch any policy pages — using built-in rules")
        return None

    # Extract rules using Claude
    try:
        rules = _extract_rules(raw_content)
        if rules and "No relevant policy" not in rules:
            _save_cache(rules, raw_content)
            print("[POLICY] Extracted and cached latest rules")
            return rules
    except Exception as e:
        print(f"[POLICY] Could not extract rules: {e}")

    return None
