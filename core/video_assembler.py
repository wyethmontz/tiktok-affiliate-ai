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

        filters.append(
            f"drawtext=text='{safe_chunk}'"
            f":fontsize=42:fontcolor=white"
            f":borderw=3:bordercolor=black"
            f":x=(w-text_w)/2:y=h-150"
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

        filters.append(
            f"drawtext=text='{safe_text}'"
            f":fontsize=44:fontcolor=white"
            f":borderw=3:bordercolor=black"
            f":x=(w-text_w)/2:y=h-150"
            f":enable='between(t,{start_time:.3f},{end_time:.3f})'"
        )

    return ",".join(filters)


def assemble_video(image_urls: list[str], voiceover_data: str | None, copy: str,
                    video_clip_urls: list[str] | None = None,
                    product_overlay_url: str | None = None,
                    user_video_urls: list[str] | None = None,
                    word_timestamps: list[dict] | None = None) -> str | None:
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

            # Calculate scene duration from voiceover length
            audio_duration = _get_audio_duration(audio_path) if audio_path else None
            crossfade_dur = 0.4  # crossfade overlap between scenes
            num_scenes = len(image_files)
            if audio_duration and num_scenes > 0:
                # Account for crossfade overlaps in total duration
                total_crossfade = crossfade_dur * max(num_scenes - 1, 0)
                scene_duration = (audio_duration + total_crossfade) / num_scenes
                print(f"[VIDEO] Voiceover is {audio_duration:.1f}s — {scene_duration:.1f}s per scene (with {crossfade_dur}s crossfades)")
            else:
                scene_duration = 5
                print(f"[VIDEO] No voiceover to sync — using {scene_duration}s per scene")

            # Different motion effect per scene for variety
            motion_effects = [
                # Scene 1: Zoom in (attention grab)
                "zoompan=z='min(zoom+0.003,1.2)':d={d}:s=1080x1920:fps=25",
                # Scene 2: Pan left to right
                "zoompan=z='1.15':x='iw/2-(iw/zoom/2)+((iw/zoom)*0.15*(on/{d}))':d={d}:s=1080x1920:fps=25",
                # Scene 3: Zoom out (reveal)
                "zoompan=z='1.2-((on/{d})*0.15)':d={d}:s=1080x1920:fps=25",
                # Scene 4: Pan right to left
                "zoompan=z='1.15':x='iw/2-(iw/zoom/2)-((iw/zoom)*0.15*(on/{d}))':d={d}:s=1080x1920:fps=25",
            ]

            for i, img_path in enumerate(image_files):
                clip_path = os.path.join(tmpdir, f"scene_{i}.mp4")
                total_frames = int(scene_duration * 25)

                # Pick motion effect (cycle through them)
                motion_template = motion_effects[i % len(motion_effects)]
                motion_filter = motion_template.format(d=total_frames)

                vf = (
                    f"scale=1200:2132:force_original_aspect_ratio=increase,"
                    f"crop=1200:2132,"
                    f"{motion_filter}"
                )

                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", img_path,
                    "-vf", vf,
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
                print(f"[VIDEO] Scene {i + 1}: {['zoom-in', 'pan-right', 'zoom-out', 'pan-left'][i % 4]}")

        if not scene_clips:
            print("[VIDEO] No scene clips generated")
            return None

        # Concatenate with crossfade transitions between scenes
        if len(scene_clips) == 1:
            concat_path = scene_clips[0]
        elif len(scene_clips) >= 2:
            # Build FFmpeg crossfade chain
            # For N clips: apply N-1 crossfade filters
            current = scene_clips[0]
            for i in range(1, len(scene_clips)):
                xfade_path = os.path.join(tmpdir, f"xfade_{i}.mp4")
                offset = scene_duration - crossfade_dur
                if offset < 0.5:
                    offset = 0.5

                xfade_cmd = [
                    "ffmpeg", "-y",
                    "-i", current,
                    "-i", scene_clips[i],
                    "-filter_complex",
                    f"xfade=transition=fadeblack:duration={crossfade_dur}:offset={offset:.2f}",
                    "-c:v", "libx264",
                    "-pix_fmt", "yuv420p",
                    xfade_path
                ]
                result = subprocess.run(xfade_cmd, capture_output=True, text=True, timeout=120)
                if result.returncode != 0:
                    print(f"[VIDEO] Crossfade {i} failed: {result.stderr[-300:]}")
                    # Fallback: simple concat without transition
                    concat_file = os.path.join(tmpdir, "concat.txt")
                    with open(concat_file, "w") as f:
                        for clip in scene_clips:
                            f.write(f"file '{clip}'\n")
                    xfade_path = os.path.join(tmpdir, "concat_fallback.mp4")
                    subprocess.run([
                        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                        "-i", concat_file, "-c", "copy", xfade_path
                    ], capture_output=True, text=True, timeout=60)
                    current = xfade_path
                    break
                current = xfade_path

            concat_path = current
            print(f"[VIDEO] Applied crossfade transitions between {len(scene_clips)} scenes")
        else:
            concat_path = scene_clips[0]

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
            # Scale word timestamps to fit actual video duration
            scaled_timestamps = word_timestamps
            if word_timestamps and len(word_timestamps) > 0:
                audio_end = word_timestamps[-1]["end"]
                if audio_end > 0 and abs(audio_end - video_duration) > 0.5:
                    scale = video_duration / audio_end
                    scaled_timestamps = [
                        {"word": w["word"], "start": w["start"] * scale, "end": w["end"] * scale}
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
