"""
get_bgm.py — BGM download helper for the Discovery pipeline.

Opens the 3 pre-picked Pixabay track pages in your default browser so you can
click Download once per page, then drop the resulting MP3s into assets/music/
with the exact filenames the pipeline expects.

Usage (from project root):
    python scripts/get_bgm.py            # opens 3 browser tabs + shows checklist
    python scripts/get_bgm.py --verify   # only checks which files are present

Why manual: Pixabay generates download URLs per session — they don't expose a
stable CDN link you can curl/wget, so full automation isn't possible without
a headless browser. Click-download-rename is the quickest reliable path.

Tracks are CC0 (commercial OK, no attribution required).
"""
import argparse
import os
import sys
import webbrowser

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MUSIC_DIR = os.path.join(HERE, "assets", "music")

TRACKS = [
    {
        "filename": "cinematic-ambient.mp3",
        "mood": "Cinematic (die-cast / action figures)",
        "url": "https://pixabay.com/music/main-title-inspirational-cinematic-ambient-after-the-storm-133540/",
        "title": "Inspirational Cinematic Ambient — After The Storm",
    },
    {
        "filename": "soft-lofi.mp3",
        "mood": "Soft (plushies)",
        "url": "https://pixabay.com/music/beats-relaxing-piano-lofi-instrumental-251401/",
        "title": "Relaxing Piano Lofi Instrumental",
    },
    {
        "filename": "lofi-beats.mp3",
        "mood": "Lofi beats (building blocks)",
        "url": "https://pixabay.com/music/beats-lofi-study-calm-peaceful-chill-hop-112191/",
        "title": "Lofi Study — Calm Peaceful Chill Hop",
    },
]


def check_files() -> tuple[list[dict], list[dict]]:
    """Return (present, missing) track lists based on filename presence in MUSIC_DIR."""
    present, missing = [], []
    for t in TRACKS:
        path = os.path.join(MUSIC_DIR, t["filename"])
        if os.path.exists(path) and os.path.getsize(path) > 1024:
            present.append(t)
        else:
            missing.append(t)
    return present, missing


def print_status(present: list[dict], missing: list[dict]) -> None:
    print(f"\nMusic folder: {MUSIC_DIR}")
    print(f"Present: {len(present)}/{len(TRACKS)}")
    for t in present:
        path = os.path.join(MUSIC_DIR, t["filename"])
        size_kb = os.path.getsize(path) // 1024
        print(f"  [OK]  {t['filename']:25} ({size_kb} KB) — {t['mood']}")
    for t in missing:
        print(f"  [--]  {t['filename']:25} — {t['mood']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true",
                        help="Only check which files are present, don't open browser.")
    args = parser.parse_args()

    if not os.path.isdir(MUSIC_DIR):
        os.makedirs(MUSIC_DIR, exist_ok=True)

    present, missing = check_files()

    if args.verify:
        print("=== BGM Verify ===")
        print_status(present, missing)
        return 0 if not missing else 1

    print("=== BGM Download Helper ===")
    print_status(present, missing)

    if not missing:
        print("\nAll 3 BGM tracks already present. Nothing to do.")
        return 0

    print(f"\nOpening {len(missing)} Pixabay page(s) in your browser...")
    for t in missing:
        print(f"  {t['url']}")
        try:
            webbrowser.open(t["url"])
        except Exception as e:
            print(f"  (could not open automatically: {e})")

    print("\nFor each page:")
    print("  1. Click the 'Download' button")
    print("  2. Save the MP3 into:", MUSIC_DIR)
    print("  3. Rename to match the filename shown in the checklist below\n")
    for t in missing:
        print(f"  - {t['title']}")
        print(f"      -> save as:  {t['filename']}")

    print("\nWhen done, verify with:  python scripts/get_bgm.py --verify")
    return 0


if __name__ == "__main__":
    sys.exit(main())
