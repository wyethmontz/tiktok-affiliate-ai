import os
import re
import base64
import tempfile
import subprocess
import httpx


def _download_file(url: str, dest: str):
    """Download a URL to a local file."""
    if url.startswith("data:"):
        # Handle base64 data URIs (voiceover)
        header, data = url.split(",", 1)
        with open(dest, "wb") as f:
            f.write(base64.b64decode(data))
    else:
        with httpx.Client(timeout=30) as client:
            res = client.get(url)
            res.raise_for_status()
            with open(dest, "wb") as f:
                f.write(res.content)


def _extract_script_text(copy: str) -> str:
    """Extract just the script portion for captions."""
    match = re.search(r'SCRIPT:\s*(.+?)(?:CTA:|HASHTAGS:|$)', copy, re.DOTALL)
    return match.group(1).strip() if match else copy.strip()


def _split_captions(text: str, num_scenes: int) -> list[str]:
    """Split script text into roughly equal parts for each scene."""
    words = text.split()
    if not words:
        return [""] * num_scenes
    chunk_size = max(1, len(words) // num_scenes)
    captions = []
    for i in range(num_scenes):
        start = i * chunk_size
        end = start + chunk_size if i < num_scenes - 1 else len(words)
        captions.append(" ".join(words[start:end]))
    return captions


def assemble_video(image_urls: list[str], voiceover_data: str | None, copy: str) -> str | None:
    """
    Assemble a TikTok-ready MP4 from images + voiceover + captions using FFmpeg.
    Returns base64 data URI of the final video, or None on failure.
    """
    if not image_urls:
        print("[VIDEO] No images to assemble")
        return None

    tmpdir = tempfile.mkdtemp(prefix="tiktok_video_")

    try:
        # Download images
        image_files = []
        for i, url in enumerate(image_urls):
            ext = ".webp" if "webp" in url else ".jpg"
            img_path = os.path.join(tmpdir, f"img_{i}{ext}")
            _download_file(url, img_path)
            image_files.append(img_path)

        # Download voiceover if available
        audio_path = None
        if voiceover_data:
            audio_path = os.path.join(tmpdir, "voiceover.mp3")
            _download_file(voiceover_data, audio_path)

        # Split script into captions per scene
        script_text = _extract_script_text(copy)
        captions = _split_captions(script_text, len(image_files))

        # Generate individual scene clips with zoom effect and captions
        scene_clips = []
        scene_duration = 6  # seconds per scene

        for i, img_path in enumerate(image_files):
            clip_path = os.path.join(tmpdir, f"scene_{i}.mp4")
            caption = captions[i] if i < len(captions) else ""

            # Escape special characters for FFmpeg drawtext
            safe_caption = caption.replace("'", "'\\''").replace(":", "\\:")

            # Ken Burns zoom effect: slowly zoom in from 1.0x to 1.15x
            zoom_filter = (
                f"scale=1080:1920:force_original_aspect_ratio=increase,"
                f"crop=1080:1920,"
                f"zoompan=z='min(zoom+0.0025,1.15)':d={scene_duration * 25}:s=1080x1920:fps=25"
            )

            # Caption filter: white text on semi-transparent dark bar at bottom
            caption_filter = ""
            if safe_caption:
                caption_filter = (
                    f",drawtext=text='{safe_caption}'"
                    f":fontsize=32:fontcolor=white"
                    f":borderw=2:bordercolor=black"
                    f":x=(w-text_w)/2:y=h-120"
                    f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                )

            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", img_path,
                "-vf", zoom_filter + caption_filter,
                "-t", str(scene_duration),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                clip_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"[VIDEO] FFmpeg scene {i} error: {result.stderr[-500:]}")
                continue

            scene_clips.append(clip_path)

        if not scene_clips:
            print("[VIDEO] No scene clips generated")
            return None

        # Create concat file for FFmpeg
        concat_file = os.path.join(tmpdir, "concat.txt")
        with open(concat_file, "w") as f:
            for clip in scene_clips:
                f.write(f"file '{clip}'\n")

        # Concatenate all scene clips
        concat_path = os.path.join(tmpdir, "concat.mp4")
        concat_cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            concat_path
        ]

        result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"[VIDEO] FFmpeg concat error: {result.stderr[-500:]}")
            return None

        # Overlay voiceover audio if available
        final_path = os.path.join(tmpdir, "final.mp4")

        if audio_path and os.path.exists(audio_path):
            audio_cmd = [
                "ffmpeg", "-y",
                "-i", concat_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                final_path
            ]
            result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"[VIDEO] FFmpeg audio overlay error: {result.stderr[-500:]}")
                # Fall back to video without audio
                final_path = concat_path
        else:
            final_path = concat_path

        # Read final video and return as base64 data URI
        with open(final_path, "rb") as f:
            video_bytes = f.read()

        video_b64 = base64.b64encode(video_bytes).decode()
        return f"data:video/mp4;base64,{video_b64}"

    except Exception as e:
        print(f"[VIDEO ERROR] {e}")
        return None

    finally:
        # Cleanup temp files
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)
