import os
import re
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
REPLICATE_VIDEO_URL = "https://api.replicate.com/v1/models/wan-video/wan-2.5-i2v/predictions"


def _convert_gdrive_url(url: str) -> str:
    """Convert Google Drive share links to direct download URLs."""
    match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
    if match:
        return f"https://drive.google.com/uc?export=download&id={match.group(1)}"
    return url


def _seconds_to_frames(seconds: float, fps: int = 16) -> int:
    """Convert target duration to frame count. Wan 2.5 supports 1-81 frames at 16fps."""
    frames = int(seconds * fps)
    return max(1, min(frames, 81))  # clamp to model limits


def _run_video_prediction(image_url: str, prompt: str, num_frames: int = 81) -> str | None:
    """Call Replicate Wan 2.5 I2V API to animate an image into a video clip."""
    headers = {
        "Authorization": f"Bearer {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    image_url = _convert_gdrive_url(image_url)
    body = {
        "input": {
            "image": image_url,
            "prompt": prompt,
            "num_frames": num_frames,
            "num_inference_steps": 30,
            "guide_scale": 5,
            "resolution": "480p",  # fast + cheap, good enough for TikTok mobile
            "aspect_ratio": "9:16",
        }
    }

    with httpx.Client(timeout=300) as client:
        # Create prediction
        res = client.post(REPLICATE_VIDEO_URL, headers=headers, json=body)
        res.raise_for_status()
        prediction = res.json()

        # Poll until done (video gen takes longer than images)
        poll_url = prediction["urls"]["get"]
        while prediction["status"] not in ("succeeded", "failed", "canceled"):
            time.sleep(5)
            res = client.get(poll_url, headers=headers)
            res.raise_for_status()
            prediction = res.json()

        if prediction["status"] == "succeeded" and prediction.get("output"):
            output = prediction["output"]
            # Output can be a URL string or a list
            if isinstance(output, list):
                return output[0]
            return output

    return None


def generate_video_clips(image_urls: list[str], media_prompts: str,
                         target_duration: float | None = None) -> list[str]:
    """
    Takes generated image URLs and their corresponding prompts,
    animates each image into a video clip using Wan 2.5 I2V.
    If target_duration is provided (total seconds from voiceover),
    each clip is sized to fill its share of the total duration.
    Returns a list of video clip URLs.
    """
    if not REPLICATE_API_TOKEN:
        print("[VIDEO GEN] No REPLICATE_API_TOKEN set, skipping")
        return []

    # Calculate frames per clip based on voiceover duration
    num_clips = len(image_urls)
    if target_duration and num_clips > 0:
        seconds_per_clip = target_duration / num_clips
        frames_per_clip = _seconds_to_frames(seconds_per_clip)
        print(f"[VIDEO GEN] Target: {target_duration:.1f}s total → {seconds_per_clip:.1f}s per clip ({frames_per_clip} frames)")
    else:
        frames_per_clip = 81  # default ~5s
        print(f"[VIDEO GEN] No duration target — using {frames_per_clip} frames (~5s per clip)")

    # Extract prompts to use as motion descriptions
    lines = re.findall(r'\d+\.\s*(.+)', media_prompts)
    lines = [re.sub(r'\*{1,2}', '', line) for line in lines]
    lines = [re.sub(r'^Scene\s*\d+:?\s*', '', line, flags=re.IGNORECASE).strip() for line in lines]
    lines = [line for line in lines if line]

    video_urls = []
    for i, image_url in enumerate(image_urls):
        # Use matching prompt if available, otherwise generic motion prompt
        prompt = lines[i] if i < len(lines) else "smooth cinematic motion, subtle movement"

        # Add motion keywords to help the model
        motion_prompt = f"{prompt}, smooth natural motion, cinematic, TikTok style vertical video"

        try:
            if i > 0:
                time.sleep(5)  # Avoid rate limiting
            print(f"[VIDEO GEN] Animating scene {i + 1}/{num_clips}...")
            url = _run_video_prediction(image_url, motion_prompt, num_frames=frames_per_clip)
            if url:
                video_urls.append(url)
                print(f"[VIDEO GEN] Scene {i + 1} done")
            else:
                print(f"[VIDEO GEN] Scene {i + 1} failed — no output")
        except Exception as e:
            if "429" in str(e):
                print("[VIDEO GEN] Rate limited, retrying in 15s...")
                time.sleep(15)
                try:
                    url = _run_video_prediction(image_url, motion_prompt, num_frames=frames_per_clip)
                    if url:
                        video_urls.append(url)
                except Exception as e2:
                    print(f"[VIDEO GEN ERROR] Retry failed: {e2}")
            else:
                print(f"[VIDEO GEN ERROR] {e}")

    return video_urls
