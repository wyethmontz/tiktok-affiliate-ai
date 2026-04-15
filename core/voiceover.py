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


def _extract_script(copy: str) -> str:
    """Extract just the script portion from copy (remove CTA/hashtags)."""
    script_match = re.search(r'SCRIPT:\s*(.+?)(?:CTA:|HASHTAGS:|$)', copy, re.DOTALL)
    text = script_match.group(1).strip() if script_match else copy.strip()
    if len(text) > 1000:
        text = text[:1000]
    return text


def generate_voiceover(copy: str, voice_id: str = DEFAULT_VOICE_ID) -> str | None:
    """
    Generate a voiceover MP3 from ad copy using ElevenLabs TTS.
    Returns the URL to the audio file (base64 data URI for now).
    """
    if not ELEVENLABS_API_KEY:
        print("[VOICEOVER] No ELEVENLABS_API_KEY set, skipping")
        return None

    text = _extract_script(copy)

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


def generate_voiceover_with_timestamps(copy: str, voice_id: str = DEFAULT_VOICE_ID) -> tuple[str | None, list[dict] | None]:
    """
    Generate voiceover WITH word-level timestamps using ElevenLabs.
    Returns (audio_data_uri, word_timestamps) where word_timestamps is:
    [{"word": "Guys", "start": 0.0, "end": 0.3}, ...]
    """
    if not ELEVENLABS_API_KEY:
        print("[VOICEOVER] No ELEVENLABS_API_KEY set, skipping")
        return None, None

    text = _extract_script(copy)

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
                f"{ELEVENLABS_TTS_URL}/{voice_id}/with-timestamps",
                headers=headers,
                json=body,
            )
            res.raise_for_status()
            data = res.json()

            # Extract audio
            audio_b64 = data.get("audio_base64", "")
            if not audio_b64:
                print("[VOICEOVER] No audio in timestamps response")
                return None, None

            audio_uri = f"data:audio/mpeg;base64,{audio_b64}"

            # Extract word timestamps
            word_timestamps = []
            alignment = data.get("alignment", {})
            characters = alignment.get("characters", [])
            char_starts = alignment.get("character_start_times_seconds", [])
            char_ends = alignment.get("character_end_times_seconds", [])

            if characters and char_starts and char_ends:
                # Group characters into words
                current_word = ""
                word_start = 0.0
                word_end = 0.0

                for i, char in enumerate(characters):
                    start = char_starts[i] if i < len(char_starts) else 0
                    end = char_ends[i] if i < len(char_ends) else 0

                    if char == " " or char == "\n":
                        if current_word.strip():
                            word_timestamps.append({
                                "word": current_word.strip(),
                                "start": word_start,
                                "end": word_end,
                            })
                        current_word = ""
                        word_start = end
                    else:
                        if not current_word:
                            word_start = start
                        current_word += char
                        word_end = end

                # Don't forget the last word
                if current_word.strip():
                    word_timestamps.append({
                        "word": current_word.strip(),
                        "start": word_start,
                        "end": word_end,
                    })

            print(f"[VOICEOVER] Generated with {len(word_timestamps)} word timestamps")
            return audio_uri, word_timestamps

    except Exception as e:
        print(f"[VOICEOVER] Timestamps failed ({e}), falling back to regular voiceover")
        # Fallback to regular voiceover without timestamps
        audio = generate_voiceover(copy, voice_id)
        return audio, None


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
