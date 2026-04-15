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
User Input (product name + product photo or video clips)
   -> Optimizer        (learns from past top-scoring ads)
   -> Strategist       (creates hook, angle, positioning + auto-detects audience/goal)
   -> Copywriter       (writes TikTok script + CTA with affiliate disclosure)
   -> Creative Director (breaks into visual scenes, 9:16 format)
   -> Compliance Agent  (checks for TikTok policy violations)
   -> [MODE A: Product Photo]
      -> Kontext Scenes (Flux Kontext Pro — generates realistic in-use scenes from product photo)
      -> Video Generator (Wan 2.5 I2V — animates scenes into motion video)
   -> [MODE B: User Video Clips]
      -> Skip image/video gen — use real phone recordings directly
   -> [MODE C: No images]
      -> Media Generator (creates AI image prompts)
      -> Image Generator (Flux Schnell — generates images)
      -> Video Generator (Wan 2.5 I2V — animates into motion video)
   -> Voiceover         (ElevenLabs TTS — Filipina voice, synced to video duration)
   -> Video Assembler   (FFmpeg — stitches clips + voiceover + captions into final MP4)
   -> Supabase          (saves everything)
   -> Frontend          (displays results with video player)
```

### TikTok AIGC Policy (Official — from support.tiktok.com)

**What counts as AIGC:**
- Images, video, audio generated or modified by AI
- AI-generated realistic human likenesses
- AI voices, AI-altered speech
- Entirely AI-generated videos/images of real or fictional people, places, events

**Labeling Requirements:**
- Creators MUST label all realistic AIGC
- Use TikTok's in-app toggle: Post Settings > More options (...) > AI-generated content ON
- Can also add text, hashtag sticker, or description disclosure
- Labeling does NOT affect video distribution

**Prohibited AIGC (even if labeled):**
- Fake authoritative sources or crisis events
- Fake endorsements by public figures
- Likeness of people under 18
- Likeness of adult private figures without permission
- Content that misleads about real events

**Project AIGC Requirements:**
Every generated ad MUST include:
1. AIGC disclosure reminder in the output
2. #AIgenerated hashtag in the tiktok_caption
3. Instruction to enable TikTok's AIGC label toggle when posting
4. #ad disclosure for affiliate transparency

### TikTok Compliance Rules (enforced by Compliance Agent)
1. No fabricated claims — no invented prices, stats, testimonials
2. Affiliate disclosure required — #ad or #sponsored in every CTA
3. AI content disclosure — #AIgenerated hashtag + AIGC label reminder
4. No fake urgency/scarcity — no "selling out fast" unless verified
5. No health/beauty claims without evidence
6. Product claims must match what user provided, nothing invented
7. No portrayal of real public figures (prohibited even if labeled)
8. No fake "in-hand" product usage passed off as real person

### Backend (Python / FastAPI)
- `api.py` — FastAPI server with all routes
- `agents/` — 8 AI agents (strategist, copywriter, creative, qa, media, compliance, voiceover, optimizer)
- `core/llm.py` — Claude API wrapper (claude-sonnet-4)
- `core/db.py` — Supabase client + save_ad()
- `core/job_store.py` — In-memory background job tracking
- `core/analytics.py` — Analytics queries
- `core/auth.py` — JWT auth middleware (Supabase Auth)
- `core/image_gen.py` — Replicate Flux API (image generation)
- `core/product_scenes.py` — Replicate Flux Kontext Pro (product-in-context scene generation)
- `core/video_gen.py` — Replicate Wan 2.5 I2V API (image-to-video animation)
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
Columns: id (uuid), product, audience, platform, goal, hook, angle, positioning, copy, creative, qa_score, qa_score_numeric (int), media, images (text), voiceover_url (text), compliance_status (text), tiktok_caption (text), created_at (timestamptz)

## Dependencies

Backend: see `requirements.txt`
Frontend: see `ai-frontend/package.json`
