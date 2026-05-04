import os
from supabase import create_client
from dotenv import load_dotenv

# Load the variables from your .env file
load_dotenv()

# -----------------------
# CONNECT TO SUPABASE
# -----------------------

# This pulls the keys you just saved in your .env file
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


# -----------------------
# SAVE AD FUNCTION
# -----------------------
def save_ad(data):
    """
    This is your bridge between Python AI system and real database.
    It takes the AI results and pushes them into the 'ads' table.
    Also auto-cleans up ads older than 7 days to stay under free tier.
    """

    response = supabase.table("ads").insert(data).execute()

    # Auto-cleanup: delete ads older than 7 days (non-blocking, best-effort)
    try:
        _auto_cleanup_old_ads()
    except Exception as e:
        print(f"[CLEANUP] Skipped: {e}")

    return response


def _auto_cleanup_old_ads(max_age_days: int = 7):
    """Delete ads older than max_age_days to keep DB under 1GB free tier."""
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
    result = supabase.table("ads").delete().lt("created_at", cutoff).execute()
    if result.data:
        print(f"[CLEANUP] Auto-deleted {len(result.data)} ads older than {max_age_days} days")
