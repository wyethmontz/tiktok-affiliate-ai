import os
import uuid
from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from workflows.ad_pipeline import run_pipeline
from workflows.regenerate_video import run_regenerate_pipeline
from core.auth import get_current_user
from core.db import supabase
from core.job_store import jobs
from core.analytics import get_summary
from agents.optimizer import run_optimizer

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter

# Serve uploaded product images
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Please slow down."},
    )


# CORS — lock to the frontend origin(s) in the ALLOWED_ORIGINS env var.
# Set in .env as a comma-separated list, e.g.:
#   ALLOWED_ORIGINS=http://localhost:3000,https://abc.trycloudflare.com
# Dev fallback includes localhost/127.0.0.1 on the default Next.js port.
_allowed = os.getenv("ALLOWED_ORIGINS", "").strip()
if _allowed:
    ALLOWED_ORIGINS = [o.strip() for o in _allowed.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


class AdRequest(BaseModel):
    product: str = Field(..., max_length=200)
    audience: str = Field("", max_length=200)
    goal: str = Field("", max_length=200)
    affiliate_link: str = Field("", max_length=500)
    product_image_urls: list[str] = Field(default_factory=list)
    user_video_urls: list[str] = Field(default_factory=list)
    use_ai_video: bool = Field(False)  # off by default to save costs
    bgm_style: str = Field("happy", max_length=20)  # happy ukulele
    # "affiliate" = basketed conversion post (default). "cinematic" = no-basket discovery post.
    style: str = Field("affiliate", max_length=20)

    @field_validator("style")
    @classmethod
    def validate_style(cls, v):
        if v not in {"affiliate", "cinematic"}:
            raise ValueError("style must be 'affiliate' or 'cinematic'")
        return v

    @field_validator("product_image_urls")
    @classmethod
    def validate_image_urls(cls, v):
        if len(v) > 4:
            raise ValueError("Maximum 4 product images allowed")
        for url in v:
            url = url.strip()
            if url and not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid image URL: {url}")
            if len(url) > 2000:
                raise ValueError("Image URL too long (max 2000 chars)")
        return v

    @field_validator("user_video_urls")
    @classmethod
    def validate_video_urls(cls, v):
        if len(v) > 5:
            raise ValueError("Maximum 5 video clips allowed")
        for url in v:
            url = url.strip()
            if url and not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid video URL: {url}")
        return v


def _run_job(job_id: str, input_data: dict):
    """Background task that runs the full ad pipeline."""
    try:
        result = run_pipeline(
            input_data,
            on_step=lambda step: jobs.update_step(job_id, step),
        )
        if isinstance(result, dict) and "error" in result:
            jobs.fail_job(job_id, result["error"])
        else:
            jobs.complete_job(job_id, result)
    except Exception as e:
        jobs.fail_job(job_id, str(e))


def _run_regenerate_job(job_id: str, ad_id: str):
    """Background task that regenerates the video for an existing ad."""
    try:
        result = run_regenerate_pipeline(
            ad_id,
            on_step=lambda step: jobs.update_step(job_id, step),
        )
        if isinstance(result, dict) and "error" in result:
            jobs.fail_job(job_id, result["error"])
        else:
            jobs.complete_job(job_id, result)
    except Exception as e:
        jobs.fail_job(job_id, str(e))


ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/quicktime", "video/webm", "video/x-msvideo"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB


@app.post("/upload-image")
@limiter.limit("20/minute")
async def upload_image(request: Request, file: UploadFile = File(...),
                       user=Depends(get_current_user)):
    """Upload a product image and return its URL."""
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, and GIF images allowed")

    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE:
        raise HTTPException(status_code=400, detail="Image too large (max 5MB)")

    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/uploads/{filename}"

    return {"url": image_url, "filename": filename}


@app.post("/upload-video")
@limiter.limit("10/minute")
async def upload_video(request: Request, file: UploadFile = File(...),
                       user=Depends(get_current_user)):
    """Upload a video clip and return its URL."""
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="Only MP4, MOV, WebM, and AVI videos allowed")

    contents = await file.read()
    if len(contents) > MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="Video too large (max 50MB)")

    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "mp4"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        f.write(contents)

    base_url = str(request.base_url).rstrip("/")
    video_url = f"{base_url}/uploads/{filename}"

    return {"url": video_url, "filename": filename}


@app.post("/generate-ad")
@limiter.limit("5/minute")
def generate_ad(request: Request, ad: AdRequest, background_tasks: BackgroundTasks,
                user=Depends(get_current_user)):
    input_data = {
        "product": ad.product.strip(),
        "audience": ad.audience.strip(),
        "platform": "TikTok",
        "goal": ad.goal.strip(),
        "affiliate_link": ad.affiliate_link.strip(),
        "product_image_urls": [url.strip() for url in ad.product_image_urls if url.strip()],
        "user_video_urls": [url.strip() for url in ad.user_video_urls if url.strip()],
        "use_ai_video": ad.use_ai_video,
        "bgm_style": ad.bgm_style,
        "style": ad.style,
    }

    job_id = jobs.create_job(input_data)
    background_tasks.add_task(_run_job, job_id, input_data)

    return {"job_id": job_id, "status": "pending"}


@app.post("/regenerate-video/{ad_id}")
@limiter.limit("5/minute")
def regenerate_video(request: Request, ad_id: str, background_tasks: BackgroundTasks,
                     user=Depends(get_current_user)):
    """Regenerate video for an existing ad — reuses approved script, only redoes visuals."""
    job_id = jobs.create_job({"ad_id": ad_id, "action": "regenerate"})
    background_tasks.add_task(_run_regenerate_job, job_id, ad_id)
    return {"job_id": job_id, "status": "pending"}


@app.get("/jobs/{job_id}")
@limiter.limit("60/minute")
def get_job(request: Request, job_id: str):
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.get("/ads")
@limiter.limit("30/minute")
def list_ads(request: Request, search: str = ""):
    if len(search) > 100:
        raise HTTPException(status_code=400, detail="Search query too long")
    # Only select small fields for list view — skip huge base64 blobs (video_url, voiceover_url)
    columns = "id,product,audience,platform,goal,hook,angle,positioning,copy,creative,qa_score,qa_score_numeric,media,images,compliance_status,tiktok_caption,created_at"
    query = supabase.table("ads").select(columns).order("created_at", desc=True).limit(50)
    if search:
        query = query.ilike("product", f"%{search}%")
    return query.execute().data


@app.get("/ads/{ad_id}")
@limiter.limit("30/minute")
def get_ad(request: Request, ad_id: str):
    result = supabase.table("ads").select("*").eq("id", ad_id).single().execute()
    return result.data


@app.get("/analytics/summary")
@limiter.limit("15/minute")
def analytics_summary(request: Request):
    return get_summary()


@app.get("/analytics/insights")
@limiter.limit("5/minute")
def analytics_insights(request: Request):
    try:
        insights = run_optimizer()
        return {"insights": insights or "Not enough data yet. Generate at least 3 ads."}
    except Exception as e:
        return {"insights": f"Could not generate insights: {str(e)}"}


@app.get("/health")
def health():
    return {"status": "ok"}
