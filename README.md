# TikTok Affiliate AI

An AI-powered pipeline that generates TikTok-compliant affiliate ad content from a single product brief. Generates strategy, script, visual scenes, AI images, voiceover, and compliance checks — all ready to post.

## How It Works

```
User Input (product, audience, goal)
    |
    v
Optimizer Agent -------> Learns from past top-scoring TikTok ads
    |
    v
Strategist Agent ------> Creates TikTok-native hook, angle, format (GRWM, POV, etc.)
    |
    v
Copywriter Agent ------> Writes TikTok script with affiliate disclosure (#ad)
    |
    v
Creative Director -----> 4 visual scenes, 9:16 vertical, under 30 seconds
    |
    v
Compliance Agent ------> Checks for TikTok policy violations
    |
    v
Media Generator -------> Creates Flux image prompts (TikTok-optimized)
    |
    v
Image Generator -------> Generates actual 9:16 images via Replicate/Flux
    |
    v
Voiceover Generator ---> Narration audio via ElevenLabs TTS
    |
    v
Supabase --------------> Saves everything to PostgreSQL
    |
    v
Dashboard -------------> Displays results with audio player + compliance badge
```

## Features

- **8 AI Agents** — Strategist, Copywriter, Creative Director, QA, Media, Compliance, Voiceover, Optimizer
- **TikTok-Native** — GRWM, POV, storytime, unboxing formats built into the strategy
- **Compliance Built-In** — Checks for fabricated claims, missing #ad disclosure, fake urgency, health claims
- **AI Image Generation** — Flux Schnell via Replicate (9:16 vertical TikTok format)
- **AI Voiceover** — ElevenLabs TTS narration from the script
- **Self-Improving** — Optimizer learns from highest-scoring ads
- **Affiliate Ready** — Auto-includes #ad disclosure, optional affiliate link field
- **Background Processing** — Async pipeline with real-time progress polling
- **Searchable History** — Browse past ads, filter by product, one-click reuse
- **Analytics Dashboard** — Score charts, top hooks, AI-generated insights

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI / LLM | Claude API (Anthropic), claude-sonnet-4 |
| Image Gen | Flux Schnell via Replicate API |
| Voiceover | ElevenLabs TTS API |
| Backend | Python, FastAPI, Pydantic |
| Frontend | TypeScript, Next.js (App Router), Tailwind CSS |
| Database | Supabase (PostgreSQL) |
| Auth | Supabase Auth (JWT) |
| Charts | Recharts |
| Security | slowapi (rate limiting), input validation, compliance agent |
| DevOps | Docker, docker-compose |

## Quick Start

### Local Development

**Backend:**
```bash
python -m venv venv
source venv/Scripts/activate    # Windows
pip install -r requirements.txt
uvicorn api:app --reload
```

**Frontend:**
```bash
cd ai-frontend
npm install
npm run dev
```

Open http://localhost:3000

### Docker

```bash
docker-compose up --build
```

### Environment Variables

Backend `.env`:
```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
REPLICATE_API_TOKEN=r8_...
ELEVENLABS_API_KEY=...
```

Frontend `ai-frontend/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## TikTok Compliance

The Compliance Agent automatically checks every ad for:

| Rule | What it catches |
|------|----------------|
| No fabricated claims | Invented prices, stats, percentages not in original input |
| No fake testimonials | Made-up reviews, celebrity endorsements, fake social proof |
| No fake urgency | "Selling out fast", "limited stock" without evidence |
| No health claims | Medical/miracle claims without evidence |
| Affiliate disclosure | Missing #ad or #sponsored in CTA |
| Accuracy | Claims that don't match the original product input |

Ads are tagged **PASS** or **FAIL** with specific issues and fixes listed.

## Project Structure

```
tiktok-affiliate-ai/
|-- agents/                    # AI agents
|   |-- strategist.py          # TikTok strategy (JSON output)
|   |-- copywriter.py          # TikTok script + CTA + #ad
|   |-- creative.py            # 4 scenes, 9:16, under 30s
|   |-- qa.py                  # Quality scoring (1-10)
|   |-- media.py               # Flux image prompts (TikTok-optimized)
|   |-- compliance.py          # TikTok policy compliance checker
|   |-- optimizer.py           # Learns from past ad performance
|
|-- core/                      # Core utilities
|   |-- llm.py                 # Claude API wrapper
|   |-- db.py                  # Supabase client
|   |-- image_gen.py           # Replicate Flux API (9:16 images)
|   |-- voiceover.py           # ElevenLabs TTS API
|   |-- job_store.py           # Background job tracking
|   |-- analytics.py           # Analytics queries
|   |-- auth.py                # JWT auth middleware
|
|-- workflows/
|   |-- ad_pipeline.py         # 10-step pipeline orchestration
|
|-- ai-frontend/               # Next.js frontend
|   |-- app/page.tsx           # TikTok ad generator
|   |-- app/history/page.tsx   # Searchable ad history
|   |-- app/analytics/page.tsx # Dashboard with charts
|   |-- app/login/page.tsx     # Authentication
|
|-- api.py                     # FastAPI server
|-- docker-compose.yml         # One-command deployment
|-- Dockerfile                 # Backend container
```

## Database Auto-Cleanup

The pipeline automatically manages Supabase storage to stay under the 1GB free tier:

- **Auto-cleanup on every generation** — when a new ad is saved, ads older than **7 days** are automatically deleted
- **Manual cleanup scripts** (in `scripts/`):
  - `check_images.py` — scan DB for broken image URLs (localhost, expired)
  - `cleanup_supabase.py` — delete broken URLs + ads older than 7 days

```bash
python scripts/check_images.py      # see what's broken
python scripts/cleanup_supabase.py  # delete broken + old ads
```

**Why 7 days?** Replicate image URLs expire after 1 hour, so older ads have broken images anyway. Keeping 7 days of history is plenty for reviewing recent performance before posting.

## Roadmap

- [ ] AI video generation (Kling/Runway) — turn scenes into TikTok-ready video clips
- [ ] Auto-captioning — burn captions into video (FFmpeg + Whisper)
- [ ] TikTok Shop product import — paste URL, auto-fill product details
- [ ] Batch generation — generate 5-10 ad variations per product
- [ ] Performance feedback loop — track which hooks/angles convert
