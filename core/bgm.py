import os
import subprocess

# Bundled royalty-free music tracks (Pixabay License — free commercial use, no attribution)
MUSIC_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "music")

BGM_TRACKS = {
    # Affiliate default — cheerful, ad-friendly
    "happy": {
        "file": "happy-ukulele.mp3",
        "description": "Happy ukulele — playful, cheerful, perfect for toy affiliate ads",
    },
    # Discovery moods — matched to SCENE_BUCKETS for algorithmic coherence
    "cinematic": {
        "file": "cinematic-ambient.mp3",
        "description": "Cinematic ambient — die-cast cars, action figures, premium collector vibe",
    },
    "soft": {
        "file": "soft-lofi.mp3",
        "description": "Soft lo-fi piano — plushies, cozy/cute aesthetic",
    },
    "lofi": {
        "file": "lofi-beats.mp3",
        "description": "Chill lo-fi beats — building blocks, focused/creative vibe",
    },
}

DEFAULT_TRACK = "happy"


def generate_bgm(duration: float, output_path: str, style: str = DEFAULT_TRACK) -> bool:
    """
    Prepare a background music track trimmed to the video duration.
    Uses bundled royalty-free music files.
    Returns True if successful.
    """
    if style not in BGM_TRACKS:
        style = DEFAULT_TRACK

    track = BGM_TRACKS[style]
    source_path = os.path.join(MUSIC_DIR, track["file"])

    if not os.path.exists(source_path):
        print(f"[BGM] Music file not found: {source_path}")
        return False

    # Trim (or loop) the track to match video duration, fade out at the end
    cmd = [
        "ffmpeg", "-y",
        "-stream_loop", "-1",  # loop if track is shorter than video
        "-i", source_path,
        "-t", str(duration),
        "-af", f"afade=t=out:st={max(duration - 2, 0):.1f}:d=2,volume=0.4",
        "-c:a", "aac",
        "-b:a", "128k",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"[BGM] Prepared {track['description']} ({duration:.1f}s)")
            return True
        else:
            print(f"[BGM] FFmpeg error: {result.stderr[-300:]}")
    except Exception as e:
        print(f"[BGM] Error: {e}")

    return False


def get_available_styles() -> dict:
    """Return available BGM tracks and descriptions."""
    return {k: v["description"] for k, v in BGM_TRACKS.items()}
