from fastapi import FastAPI, BackgroundTasks, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from workflows.ad_pipeline import run_pipeline
from core.db import save_ad, supabase
from core.job_store import jobs
from core.analytics import get_summary
from agents.optimizer import run_optimizer

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI()
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"error": "Too many requests. Please slow down."},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AdRequest(BaseModel):
    product: str = Field(..., max_length=200)
    audience: str = Field(..., max_length=200)
    goal: str = Field(..., max_length=200)
    affiliate_link: str = Field("", max_length=500)
    product_image_urls: list[str] = Field(default_factory=list)

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


@app.post("/generate-ad")
@limiter.limit("5/minute")
def generate_ad(request: Request, ad: AdRequest, background_tasks: BackgroundTasks):
    input_data = {
        "product": ad.product.strip(),
        "audience": ad.audience.strip(),
        "platform": "TikTok",
        "goal": ad.goal.strip(),
        "affiliate_link": ad.affiliate_link.strip(),
        "product_image_urls": [url.strip() for url in ad.product_image_urls if url.strip()],
    }

    job_id = jobs.create_job(input_data)
    background_tasks.add_task(_run_job, job_id, input_data)

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
    query = supabase.table("ads").select("*").order("created_at", desc=True)
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
