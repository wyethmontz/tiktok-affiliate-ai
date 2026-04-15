import os
import subprocess
import random

# Background music styles — generated with FFmpeg (no external files needed)
# Each style produces a different vibe using sine wave synthesis + filters
BGM_STYLES = {
    "lofi": {
        "description": "Chill lo-fi beat — relaxed, casual TikTok vibe",
        # Soft chord progression with reverb
        "filter": (
            "sine=f=261.63:d={dur},sine=f=329.63:d={dur},sine=f=392:d={dur},"
            "amix=inputs=3:duration=first,"
            "tremolo=f=2:d=0.4,"
            "aecho=0.8:0.88:60:0.4,"
            "lowpass=f=800,"
            "volume=0.12"
        ),
    },
    "upbeat": {
        "description": "Energetic upbeat — exciting product reveal",
        # Higher pitched, faster rhythm
        "filter": (
            "sine=f=523.25:d={dur},sine=f=659.25:d={dur},sine=f=783.99:d={dur},"
            "amix=inputs=3:duration=first,"
            "tremolo=f=4:d=0.6,"
            "aecho=0.6:0.6:40:0.3,"
            "lowpass=f=1200,"
            "volume=0.12"
        ),
    },
    "soft": {
        "description": "Soft ambient — gentle product showcase",
        # Very soft low tones
        "filter": (
            "sine=f=196:d={dur},sine=f=246.94:d={dur},"
            "amix=inputs=2:duration=first,"
            "tremolo=f=1.5:d=0.3,"
            "aecho=0.8:0.9:80:0.5,"
            "lowpass=f=600,"
            "volume=0.10"
        ),
    },
}

DEFAULT_STYLE = "lofi"


def generate_bgm(duration: float, output_path: str, style: str = DEFAULT_STYLE) -> bool:
    """
    Generate a background music track using FFmpeg audio synthesis.
    No external files needed — creates music from sine waves + effects.
    Returns True if successful.
    """
    if style not in BGM_STYLES:
        style = DEFAULT_STYLE

    bgm = BGM_STYLES[style]
    audio_filter = bgm["filter"].format(dur=duration)

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", audio_filter,
        "-t", str(duration),
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"[BGM] Generated {style} background music ({duration:.1f}s)")
            return True
        else:
            print(f"[BGM] FFmpeg error: {result.stderr[-300:]}")
    except Exception as e:
        print(f"[BGM] Error: {e}")

    return False


def get_available_styles() -> dict:
    """Return available BGM styles and descriptions."""
    return {k: v["description"] for k, v in BGM_STYLES.items()}
