import os
import re
import base64
import tempfile
import subprocess
import httpx
from dotenv import load_dotenv

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech"

# Filipina voices for TikTok toy/affiliate promos
VOICE_OPTIONS = {
    "jessica": "cgSgspJ2msm6clMCkdW9",       # Playful & bright — high energy toy promos
    "ate_donnah": "xBXX3d8DJAMukmVFzDUY",     # Cutest voice — adorable unboxings
    "anika": "RABOvaPec1ymXz02oDQi",          # Sweet & lively — TikTok hooks
    "lola_felicidad": "gILcvhAz18uV9ARSsU4u", # Storyteller — educational toys
    "boses_cartoons": "gA870ILGhb2a1FhxtmLH",  # Animated character voice
}
DEFAULT_VOICE_ID = VOICE_OPTIONS["jessica"]  # best for upbeat TikTok affiliate content


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
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.55,
            "style": 0.55,
            "use_speaker_boost": True,
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

            audio_b64 = base64.b64encode(res.content).decode()
            return f"data:audio/mpeg;base64,{audio_b64}"

    except Exception as e:
        print(f"[VOICEOVER ERROR] {e}")
        return None


def get_voiceover_duration(data_uri: str) -> float | None:
    """Get the duration of a voiceover from its base64 data URI using ffprobe."""
    if not data_uri or not data_uri.startswith("data:"):
        return None

    try:
        _, b64_data = data_uri.split(",", 1)
        audio_bytes = base64.b64decode(b64_data)

        # Write to temp file for ffprobe
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", tmp_path],
            capture_output=True, text=True, timeout=10
        )
        os.unlink(tmp_path)

        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        print(f"[VOICEOVER] Could not get duration: {e}")
    return None
