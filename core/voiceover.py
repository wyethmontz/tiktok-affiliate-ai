import os
import re
import httpx
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Default voice: "Sarah" — mature, confident (available on free tier)
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"


def generate_voiceover(copy: str, voice_id: str = DEFAULT_VOICE_ID) -> str | None:
    """
    Generate a voiceover MP3 from ad copy using ElevenLabs TTS.
    Returns the URL to the audio file (base64 data URI for now).
    """
    if not ELEVENLABS_API_KEY:
        print("[VOICEOVER] No ELEVENLABS_API_KEY set, skipping")
        return None

    # Extract just the script portion (remove CTA/hashtags for voiceover)
    script_match = re.search(r'SCRIPT:\s*(.+?)(?:CTA:|HASHTAGS:|$)', copy, re.DOTALL)
    text = script_match.group(1).strip() if script_match else copy.strip()

    # Limit length for TTS
    if len(text) > 1000:
        text = text[:1000]

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.4,
            "similarity_boost": 0.75,
        }
    }

    try:
        with httpx.Client(timeout=30) as client:
            res = client.post(
                f"{ELEVENLABS_TTS_URL}/{voice_id}",
                headers=headers,
                json=body,
            )
            res.raise_for_status()

            # Save audio to a temp file and return path
            import base64
            audio_b64 = base64.b64encode(res.content).decode()
            return f"data:audio/mpeg;base64,{audio_b64}"

    except Exception as e:
        print(f"[VOICEOVER ERROR] {e}")
        return None
