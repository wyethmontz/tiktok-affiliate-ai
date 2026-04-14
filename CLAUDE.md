# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project

TikTok Affiliate AI — an AI-powered pipeline that generates TikTok-compliant affiliate ad content from a single product brief. Generates strategy, copy, visual scenes, images, and voiceover — all ready to post.

## Setup

### Backend
```bash
cd tiktok-affiliate-ai
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn api:app --reload
```

### Frontend
```bash
cd ai-frontend
npm install
npm run dev
```

### Docker (runs both)
```bash
docker-compose up --build
```

### Environment variables
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

## Architecture

TikTok-compliant affiliate ad generation pipeline with 8 agents:

```
User Input (product, audience, goal, affiliate_link)
   -> Optimizer        (learns from past top-scoring ads)
   -> Strategist       (creates hook, angle, positioning — TikTok-native)
   -> Copywriter       (writes TikTok script + CTA with affiliate disclosure)
   -> Creative Director (breaks into 4-5 visual scenes, 9:16 format)
   -> Compliance Agent  (checks for TikTok policy violations)
   -> Media Generator   (creates AI image prompts optimized for TikTok)
   -> Image Generator   (Flux via Replicate — generates actual images)
   -> Voiceover         (ElevenLabs TTS — generates narration audio)
   -> Supabase          (saves everything)
   -> Frontend          (displays results with audio player)
```

### TikTok Compliance Rules (enforced by Compliance Agent)
1. No fabricated claims — no invented prices, stats, testimonials
2. Affiliate disclosure required — #ad or #sponsored in every CTA
3. AI content disclosure — label AI-generated content
4. No fake urgency/scarcity — no "selling out fast" unless verified
5. No health/beauty claims without evidence
6. Product claims must match what user provided, nothing invented

### Backend (Python / FastAPI)
- `api.py` — FastAPI server with all routes
- `agents/` — 8 AI agents (strategist, copywriter, creative, qa, media, compliance, voiceover, optimizer)
- `core/llm.py` — Claude API wrapper (claude-sonnet-4)
- `core/db.py` — Supabase client + save_ad()
- `core/job_store.py` — In-memory background job tracking
- `core/analytics.py` — Analytics queries
- `core/auth.py` — JWT auth middleware (Supabase Auth)
- `core/image_gen.py` — Replicate Flux API (image generation)
- `core/voiceover.py` — ElevenLabs TTS API (voiceover generation)
- `workflows/ad_pipeline.py` — 10-step pipeline orchestration

### Frontend (TypeScript / Next.js)
- `app/page.tsx` — Generate Ad page (form + polling + results)
- `app/history/page.tsx` — Searchable ad history with cards
- `app/analytics/page.tsx` — Dashboard with charts (recharts)
- `app/login/page.tsx` — Supabase Auth login/signup
- `app/components/` — Sidebar, AdCard, SearchBar, AuthGuard

### API Endpoints
- `POST /generate-ad` — Starts pipeline (returns job_id, async)
- `GET /jobs/{job_id}` — Poll job status and progress
- `GET /ads` — List ads (supports ?search= filter)
- `GET /ads/{ad_id}` — Get single ad
- `GET /analytics/summary` — Dashboard stats
- `GET /analytics/insights` — AI-generated insights

## Security Checklist

1. **Rate limiting** — Every public endpoint must have rate limits
2. **Input validation** — All user inputs must have max length
3. **CORS** — Lock down to specific frontend origin in production
4. **Auth on sensitive routes** — Use `core/auth.py` dependency
5. **API keys** — Never hardcode. Always use .env files
6. **HTTPS** — Required for any public deployment

## Database (Supabase)

Table: `ads`
Columns: id (uuid), product, audience, platform, goal, hook, angle, positioning, copy, creative, qa_score, qa_score_numeric (int), media, images (text), voiceover_url (text), compliance_status (text), created_at (timestamptz)

## Dependencies

Backend: see `requirements.txt`
Frontend: see `ai-frontend/package.json`
