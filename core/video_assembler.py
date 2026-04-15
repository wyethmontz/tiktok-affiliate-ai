import os
import re
import base64
import tempfile
import subprocess
import httpx


def _convert_gdrive_url(url: str) -> str:
    """Convert Google Drive share links to direct download URLs."""
    match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if match:
        return f"https://drive.google.com/uc?export=download&id={match.group(1)}"
    return url


def _download_file(url: str, dest: str):
    """Download a URL to a local file."""
    if url.startswith("data:"):
        # Handle base64 data URIs (voiceover)
        header, data = url.split(",", 1)
        with open(dest, "wb") as f:
            f.write(base64.b64decode(data))
    else:
        url = _convert_gdrive_url(url)
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            res = client.get(url)
            res.raise_for_status()
            with open(dest, "wb") as f:
                f.write(res.content)


def _extract_script_text(copy: str) -> str:
    """Extract just the script portion for captions."""
    match = re.search(r'SCRIPT:\s*(.+?)(?:CTA:|HASHTAGS:|$)', copy, re.DOTALL)
    return match.group(1).strip() if match else copy.strip()


def _get_audio_duration(audio_path: str) -> float | None:
    """Get duration of an audio file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception as e:
        print(f"[VIDEO] Could not probe audio duration: {e}")
    return None


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


def _get_video_duration(video_path: str) -> float | None:
    """Get duration of a video file in seconds using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", video_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except Exception:
        pass
    return None


def _build_caption_filter(text: str, total_duration: float) -> str:
    """
    Build FFmpeg drawtext filter that shows captions in timed chunks,
    TikTok-style: 3-5 words at a time, centered at bottom.
    """
    words = text.split()
    if not words or total_duration <= 0:
        return ""

    # Group into chunks of 3-4 words
    chunk_size = 3
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i:i + chunk_size]))

    if not chunks:
        return ""

    time_per_chunk = total_duration / len(chunks)
    filters = []

    for i, chunk in enumerate(chunks):
        start_time = i * time_per_chunk
        end_time = start_time + time_per_chunk
        safe_chunk = chunk.replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")

        filters.append(
            f"drawtext=text='{safe_chunk}'"
            f":fontsize=42:fontcolor=white"
            f":borderw=3:bordercolor=black"
            f":x=(w-text_w)/2:y=h-150"
            f":enable='between(t,{start_time:.2f},{end_time:.2f})'"
        )

    return ",".join(filters)


def assemble_video(image_urls: list[str], voiceover_data: str | None, copy: str,
                    video_clip_urls: list[str] | None = None,
                    product_overlay_url: str | None = None,
                    user_video_urls: list[str] | None = None) -> str | None:
    """
    Assemble a TikTok-ready MP4 from user video clips, AI video clips, or images + voiceover + captions.
    Priority: user_video_urls > video_clip_urls > image_urls (Ken Burns fallback).
    Returns base64 data URI of the final video, or None on failure.
    """
    if not user_video_urls and not video_clip_urls and not image_urls:
        print("[VIDEO] No content to assemble")
        return None

    tmpdir = tempfile.mkdtemp(prefix="tiktok_video_")
    use_user_videos = bool(user_video_urls)
    use_video_clips = bool(video_clip_urls) and not use_user_videos

    try:
        # Download voiceover if available
        audio_path = None
        if voiceover_data:
            audio_path = os.path.join(tmpdir, "voiceover.mp3")
            _download_file(voiceover_data, audio_path)

        scene_clips = []

        if use_user_videos:
            # === USER VIDEO MODE: real phone recordings ===
            print(f"[VIDEO] Using {len(user_video_urls)} user video clips")
            for i, url in enumerate(user_video_urls):
                clip_path = os.path.join(tmpdir, f"user_clip_{i}.mp4")
                _download_file(url, clip_path)

                # Normalize: scale to 1080x1920 (9:16), consistent codec/fps
                normalized_path = os.path.join(tmpdir, f"scene_{i}.mp4")
                normalize_cmd = [
                    "ffmpeg", "-y",
                    "-i", clip_path,
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", "25",
                    "-an",  # strip original audio — voiceover replaces it
                    normalized_path
                ]
                result = subprocess.run(normalize_cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    print(f"[VIDEO] FFmpeg normalize user clip {i} error: {result.stderr[-500:]}")
                    continue

                scene_clips.append(normalized_path)
                print(f"[VIDEO] User clip {i + 1} normalized")

        elif use_video_clips:
            # === AI VIDEO CLIP MODE: download AI-generated video clips ===
            print(f"[VIDEO] Using {len(video_clip_urls)} AI-generated video clips")
            for i, url in enumerate(video_clip_urls):
                clip_path = os.path.join(tmpdir, f"clip_{i}.mp4")
                _download_file(url, clip_path)

                # Normalize to consistent format for concat (re-encode to same codec/fps)
                normalized_path = os.path.join(tmpdir, f"scene_{i}.mp4")
                normalize_cmd = [
                    "ffmpeg", "-y",
                    "-i", clip_path,
                    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", "25",
                    "-an",  # strip original audio, we'll add voiceover
                    normalized_path
                ]
                result = subprocess.run(normalize_cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    print(f"[VIDEO] FFmpeg normalize clip {i} error: {result.stderr[-500:]}")
                    continue

                scene_clips.append(normalized_path)
        else:
            # === IMAGE MODE: static images with Ken Burns zoom (fallback) ===
            print(f"[VIDEO] Using {len(image_urls)} static images (fallback mode)")
            image_files = []
            for i, url in enumerate(image_urls):
                ext = ".webp" if "webp" in url else ".jpg"
                img_path = os.path.join(tmpdir, f"img_{i}{ext}")
                _download_file(url, img_path)
                image_files.append(img_path)

            # Calculate scene duration from voiceover length
            audio_duration = _get_audio_duration(audio_path) if audio_path else None
            if audio_duration and len(image_files) > 0:
                scene_duration = audio_duration / len(image_files)
                print(f"[VIDEO] Voiceover is {audio_duration:.1f}s — {scene_duration:.1f}s per scene")
            else:
                scene_duration = 6
                print(f"[VIDEO] No voiceover to sync — using {scene_duration}s per scene")

            for i, img_path in enumerate(image_files):
                clip_path = os.path.join(tmpdir, f"scene_{i}.mp4")

                total_frames = int(scene_duration * 25)
                zoom_step = 0.15 / max(total_frames, 1)
                zoom_filter = (
                    f"scale=1080:1920:force_original_aspect_ratio=increase,"
                    f"crop=1080:1920,"
                    f"zoompan=z='min(zoom+{zoom_step:.6f},1.15)':d={total_frames}:s=1080x1920:fps=25"
                )

                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", img_path,
                    "-vf", zoom_filter,
                    "-t", str(scene_duration),
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-r", "25",
                    clip_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
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

        # Burn timed captions onto the video (TikTok-style word chunks)
        script_text = _extract_script_text(copy)
        video_duration = _get_video_duration(final_path)
        if script_text and video_duration:
            caption_filter = _build_caption_filter(script_text, video_duration)
            if caption_filter:
                captioned_path = os.path.join(tmpdir, "captioned.mp4")
                caption_cmd = [
                    "ffmpeg", "-y",
                    "-i", final_path,
                    "-vf", caption_filter,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "copy",
                    captioned_path
                ]
                result = subprocess.run(caption_cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    final_path = captioned_path
                    print(f"[VIDEO] Captions burned onto video")
                else:
                    print(f"[VIDEO] Caption burn failed, using video without captions: {result.stderr[-300:]}")

        # Overlay product image in the last 3 seconds (CTA moment)
        if product_overlay_url:
            video_duration = _get_video_duration(final_path) or 0
            if video_duration > 3:
                overlay_start = video_duration - 3
                product_img_path = os.path.join(tmpdir, "product_overlay.png")
                try:
                    _download_file(product_overlay_url, product_img_path)
                    overlay_path = os.path.join(tmpdir, "with_overlay.mp4")
                    # Product image: scaled to 280px wide, positioned top-right with padding
                    overlay_filter = (
                        f"[1:v]scale=280:-1[prod];"
                        f"[0:v][prod]overlay=W-w-30:30"
                        f":enable='between(t,{overlay_start:.2f},{video_duration:.2f})'"
                    )
                    overlay_cmd = [
                        "ffmpeg", "-y",
                        "-i", final_path,
                        "-i", product_img_path,
                        "-filter_complex", overlay_filter,
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-c:a", "copy",
                        overlay_path
                    ]
                    result = subprocess.run(overlay_cmd, capture_output=True, text=True, timeout=120)
                    if result.returncode == 0:
                        final_path = overlay_path
                        print(f"[VIDEO] Product overlay added at {overlay_start:.1f}s")
                    else:
                        print(f"[VIDEO] Product overlay failed: {result.stderr[-300:]}")
                except Exception as e:
                    print(f"[VIDEO] Product overlay error: {e}")

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
