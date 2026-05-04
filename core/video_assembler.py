import os
import re
import base64
import tempfile
import subprocess
import httpx
from core.bgm import generate_bgm


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


def _build_cta_overlay_filter(text: str, start: float = 0.5,
                              duration: float = 2.5) -> str:
    """
    Build a small "Follow for more" style overlay near the top of the video,
    visible only for the first few seconds. Used for Discovery posts where
    the visual is silent and the account needs explicit follower CTAs.

    Font note: Docker image ships only dejavu-core which has NO emoji glyphs.
    Keep the text ASCII/basic-latin only. Emojis will render as tofu boxes.
    """
    if not text:
        return ""

    safe_text = text.replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")
    end = start + duration

    return (
        f"drawtext=text='{safe_text}'"
        f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        f":fontsize=44:fontcolor=white"
        f":borderw=3:bordercolor=black"
        f":box=1:boxcolor=black@0.55:boxborderw=10"
        f":x=(w-text_w)/2:y=h*0.08"
        f":enable='between(t,{start:.2f},{end:.2f})'"
    )


def _build_caption_filter(text: str, total_duration: float,
                          word_timestamps: list[dict] | None = None) -> str:
    """
    Build FFmpeg drawtext filter for TikTok-style captions.
    If word_timestamps are provided, captions are synced to the voiceover.
    Otherwise falls back to evenly-timed chunks.
    """
    if word_timestamps:
        return _build_synced_caption_filter(word_timestamps)

    # Fallback: evenly-timed chunks
    words = text.split()
    if not words or total_duration <= 0:
        return ""

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

        # TikTok-style: bold, large, white text with dark box background
        filters.append(
            f"drawtext=text='{safe_chunk}'"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f":fontsize=58:fontcolor=white"
            f":borderw=4:bordercolor=black"
            f":box=1:boxcolor=black@0.5:boxborderw=12"
            f":x=(w-text_w)/2:y=h*0.62"
            f":enable='between(t,{start_time:.2f},{end_time:.2f})'"
        )

    return ",".join(filters)


def _build_synced_caption_filter(word_timestamps: list[dict]) -> str:
    """
    Build FFmpeg drawtext filter synced to actual voiceover word timings.
    Groups 2-3 words together, timed exactly to when they're spoken.
    """
    if not word_timestamps:
        return ""

    # Group words into chunks of 2-3, using actual timestamps
    chunk_size = 3
    filters = []

    for i in range(0, len(word_timestamps), chunk_size):
        chunk_words = word_timestamps[i:i + chunk_size]
        text = " ".join(w["word"] for w in chunk_words)
        start_time = chunk_words[0]["start"]
        end_time = chunk_words[-1]["end"] + 0.1  # tiny buffer

        safe_text = text.replace("'", "'\\''").replace(":", "\\:").replace("%", "%%")

        # TikTok-style: bold, large, white text with dark box background
        filters.append(
            f"drawtext=text='{safe_text}'"
            f":fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            f":fontsize=58:fontcolor=white"
            f":borderw=4:bordercolor=black"
            f":box=1:boxcolor=black@0.5:boxborderw=12"
            f":x=(w-text_w)/2:y=h*0.62"
            f":enable='between(t,{start_time:.3f},{end_time:.3f})'"
        )

    return ",".join(filters)


def assemble_video(image_urls: list[str], voiceover_data: str | None, copy: str,
                    video_clip_urls: list[str] | None = None,
                    product_overlay_url: str | None = None,
                    user_video_urls: list[str] | None = None,
                    word_timestamps: list[dict] | None = None,
                    bgm_style: str = "lofi",
                    cta_overlay_text: str | None = None) -> str | None:
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
            # === CAPCUT-STYLE MODE: images with varied motion + crossfade transitions ===
            print(f"[VIDEO] CapCut-style editing for {len(image_urls)} images")
            image_files = []
            for i, url in enumerate(image_urls):
                ext = ".webp" if "webp" in url else ".jpg"
                img_path = os.path.join(tmpdir, f"img_{i}{ext}")
                _download_file(url, img_path)
                image_files.append(img_path)

            # Calculate total video duration (matches voiceover or default 16s)
            audio_duration = _get_audio_duration(audio_path) if audio_path else None
            num_images = len(image_files)
            total_video_duration = audio_duration if audio_duration else 16.0

            # Double-pass Ken Burns: each source image is rendered TWICE with
            # different zoom motions, then interleaved (A1, B1, C1, D1, A2,
            # B2, C2, D2). Result: 8 visual cuts in the same total duration =
            # ~1.5-2s per cut vs the old ~3.5-4s. Reviewer feedback flagged
            # the slow pacing as a "scroll risk" on TikTok. Zero added image-
            # gen cost — only adds ~20-40s of FFmpeg render time per video.
            SUB_PASSES = 2
            num_scenes_total = num_images * SUB_PASSES
            sub_scene_duration = total_video_duration / num_scenes_total
            print(f"[VIDEO] Double-pass Ken Burns: {num_images} images × {SUB_PASSES} passes "
                  f"= {num_scenes_total} cuts × {sub_scene_duration:.2f}s each "
                  f"(total {total_video_duration:.1f}s)")

            # Per-pass motion: pass 1 alternates zoom-in/out, pass 2 reverses
            # (so the same image gets opposite motion the second time it appears)
            def _zoom_expr(pass_idx: int, image_idx: int, frames: int) -> tuple[str, str]:
                """Return (expr, label) for the zoom motion at this pass+image."""
                if pass_idx == 0:
                    if image_idx % 2 == 0:
                        return f"1.0+(on/{frames})*0.1", "zoom-in"
                    return f"1.1-(on/{frames})*0.1", "zoom-out"
                # Pass 2 — reversed
                if image_idx % 2 == 0:
                    return f"1.1-(on/{frames})*0.1", "zoom-out"
                return f"1.0+(on/{frames})*0.1", "zoom-in"

            # Render each image twice (pass 0 and pass 1), then interleave so
            # the cycle plays through once before any image repeats.
            clips_by_pass: list[list[str]] = [[] for _ in range(SUB_PASSES)]
            total_frames_per_clip = max(1, int(sub_scene_duration * 25))

            for pass_idx in range(SUB_PASSES):
                for i, img_path in enumerate(image_files):
                    clip_path = os.path.join(tmpdir, f"scene_p{pass_idx}_{i}.mp4")
                    zoom_expr, label = _zoom_expr(pass_idx, i, total_frames_per_clip)

                    vf = (
                        f"scale=2160:3840:force_original_aspect_ratio=increase,"
                        f"crop=2160:3840,"
                        f"zoompan=z='{zoom_expr}'"
                        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
                        f":d={total_frames_per_clip}:s=1080x1920:fps=25"
                    )

                    cmd = [
                        "ffmpeg", "-y",
                        "-loop", "1",
                        "-i", img_path,
                        "-vf", vf,
                        "-t", f"{sub_scene_duration:.3f}",
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-r", "25",
                        clip_path
                    ]

                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    if result.returncode != 0:
                        print(f"[VIDEO] FFmpeg pass {pass_idx} scene {i} error: {result.stderr[-500:]}")
                        continue

                    clips_by_pass[pass_idx].append(clip_path)
                    print(f"[VIDEO] Pass {pass_idx + 1} scene {i + 1}: {label}")

            # Interleave passes: pass 1 cycle complete, then pass 2 cycle
            for pass_clips in clips_by_pass:
                scene_clips.extend(pass_clips)

        if not scene_clips:
            print("[VIDEO] No scene clips generated")
            return None

        # Simple concat — no crossfades (they cause duration mismatch)
        concat_file = os.path.join(tmpdir, "concat.txt")
        with open(concat_file, "w") as f:
            for clip in scene_clips:
                f.write(f"file '{clip}'\n")

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
        print(f"[VIDEO] Concatenated {len(scene_clips)} scenes")

        # Generate background music
        video_len = _get_video_duration(concat_path) or 15
        bgm_path = os.path.join(tmpdir, "bgm.aac")
        has_bgm = generate_bgm(video_len, bgm_path, style=bgm_style)

        # Mix voiceover + background music onto video
        final_path = os.path.join(tmpdir, "final.mp4")

        if audio_path and os.path.exists(audio_path) and has_bgm:
            # Mix voiceover (full volume) + BGM (low volume) together
            audio_cmd = [
                "ffmpeg", "-y",
                "-i", concat_path,
                "-i", audio_path,
                "-i", bgm_path,
                "-filter_complex",
                "[1:a]adelay=500|500,volume=1.0[voice];[2:a]volume=0.3[music];[voice][music]amix=inputs=2:duration=shortest[out]",
                "-map", "0:v",
                "-map", "[out]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "128k",
                "-shortest",
                final_path
            ]
            result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                print(f"[VIDEO] BGM mix failed, trying voiceover only: {result.stderr[-300:]}")
                # Fallback: voiceover only
                audio_cmd = [
                    "ffmpeg", "-y",
                    "-i", concat_path, "-i", audio_path,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                    final_path
                ]
                subprocess.run(audio_cmd, capture_output=True, text=True, timeout=60)
            else:
                print(f"[VIDEO] Mixed voiceover + {bgm_style} background music")
        elif audio_path and os.path.exists(audio_path):
            # Voiceover only (no BGM)
            audio_cmd = [
                "ffmpeg", "-y",
                "-i", concat_path, "-i", audio_path,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                final_path
            ]
            result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                final_path = concat_path
        elif has_bgm:
            # BGM only (no voiceover)
            audio_cmd = [
                "ffmpeg", "-y",
                "-i", concat_path, "-i", bgm_path,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest",
                final_path
            ]
            result = subprocess.run(audio_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                final_path = concat_path
        else:
            final_path = concat_path

        # Burn timed captions onto the video (TikTok-style word chunks)
        script_text = _extract_script_text(copy)
        video_duration = _get_video_duration(final_path)
        if script_text and video_duration:
            # Scale word timestamps to fit actual video duration
            scaled_timestamps = word_timestamps
            if word_timestamps and len(word_timestamps) > 0:
                audio_end = word_timestamps[-1]["end"]
                if audio_end > 0 and abs(audio_end - video_duration) > 0.5:
                    scale = video_duration / audio_end
                    scaled_timestamps = [
                        {"word": w["word"], "start": (w["start"] * scale) + 0.5, "end": (w["end"] * scale) + 0.5}
                        for w in word_timestamps
                    ]
                    print(f"[VIDEO] Scaled captions from {audio_end:.1f}s to {video_duration:.1f}s")

            caption_filter = _build_caption_filter(script_text, video_duration, word_timestamps=scaled_timestamps)
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
                    print("[VIDEO] Captions burned onto video")
                else:
                    print(f"[VIDEO] Caption burn failed, using video without captions: {result.stderr[-300:]}")

        # Burn CTA overlay near the top for the first few seconds (Discovery posts).
        # Drives follower growth during the bucket-reset phase. Independent of
        # the caption burn so it runs even on silent Discovery videos.
        if cta_overlay_text:
            cta_filter = _build_cta_overlay_filter(cta_overlay_text)
            if cta_filter:
                cta_path = os.path.join(tmpdir, "with_cta.mp4")
                cta_cmd = [
                    "ffmpeg", "-y",
                    "-i", final_path,
                    "-vf", cta_filter,
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "copy",
                    cta_path
                ]
                result = subprocess.run(cta_cmd, capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    final_path = cta_path
                    print(f"[VIDEO] CTA overlay burned: {cta_overlay_text!r}")
                else:
                    print(f"[VIDEO] CTA overlay failed, continuing without: {result.stderr[-300:]}")

        # Overlay product image — TWO appearances: anchor (start, 0-1.5s) +
        # CTA reinforcement (last 3s). Start anchor builds trust before
        # AI scenes, end overlay reinforces basket-tap moment. Affiliate-only
        # (product_overlay_url is None for Discovery posts).
        if product_overlay_url:
            video_duration = _get_video_duration(final_path) or 0
            if video_duration > 3:
                anchor_end = 1.5
                cta_start = video_duration - 3
                product_img_path = os.path.join(tmpdir, "product_overlay.png")
                try:
                    _download_file(product_overlay_url, product_img_path)
                    overlay_path = os.path.join(tmpdir, "with_overlay.mp4")
                    # Product image: scaled to 280px wide, top-right with padding.
                    # ffmpeg enable expression: '+' = OR — so the overlay is visible
                    # during BOTH ranges (start anchor + end CTA).
                    overlay_filter = (
                        f"[1:v]scale=280:-1[prod];"
                        f"[0:v][prod]overlay=W-w-30:30"
                        f":enable='between(t,0,{anchor_end:.2f})"
                        f"+between(t,{cta_start:.2f},{video_duration:.2f})'"
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
                        print(f"[VIDEO] Product overlay added: anchor 0-{anchor_end}s + CTA {cta_start:.1f}-{video_duration:.1f}s")
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
