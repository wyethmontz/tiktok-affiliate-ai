import os
import subprocess
import random

# Background music styles — generated with FFmpeg (no external files needed)
# Each style produces a different vibe using sine wave synthesis + filters
BGM_STYLES = {
    "lofi": {
        "description": "Chill lo-fi beat — relaxed, casual TikTok vibe",
        "freq": 261.63,
        "tremolo_freq": 2,
        "tremolo_depth": 0.4,
        "echo_delay": 60,
        "lowpass": 800,
    },
    "upbeat": {
        "description": "Energetic upbeat — exciting product reveal",
        "freq": 523.25,
        "tremolo_freq": 4,
        "tremolo_depth": 0.6,
        "echo_delay": 40,
        "lowpass": 1200,
    },
    "soft": {
        "description": "Soft ambient — gentle product showcase",
        "freq": 196,
        "tremolo_freq": 1.5,
        "tremolo_depth": 0.3,
        "echo_delay": 80,
        "lowpass": 600,
    },
}

DEFAULT_STYLE = "upbeat"


def generate_bgm(duration: float, output_path: str, style: str = DEFAULT_STYLE) -> bool:
    """
    Generate a background music track using FFmpeg audio synthesis.
    No external files needed — creates music from sine waves + effects.
    Returns True if successful.
    """
    if style not in BGM_STYLES:
        style = DEFAULT_STYLE

    s = BGM_STYLES[style]

    # Generate two sine waves (root + fifth) and mix them for a fuller sound
    freq2 = s['freq'] * 1.5  # perfect fifth interval

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"sine=frequency={s['freq']}:duration={duration}",
        "-f", "lavfi",
        "-i", f"sine=frequency={freq2}:duration={duration}",
        "-filter_complex",
        (
            f"[0:a][1:a]amix=inputs=2:duration=first,"
            f"tremolo=f={s['tremolo_freq']}:d={s['tremolo_depth']},"
            f"aecho=0.8:0.88:{s['echo_delay']}:0.4,"
            f"lowpass=f={s['lowpass']},"
            f"volume=0.5"
        ),
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
