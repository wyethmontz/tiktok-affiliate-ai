# Discovery Pipeline Setup Guide

Post-pull checklist for the **cinematic/discovery** branch of the TikTok affiliate pipeline. Run these steps on your personal laptop after pulling the latest from GitHub.

---

## Why this exists

TikTok throttles videos with baskets attached (routes them to a smaller commerce audience), which tanked reach on posts after views 336/387. This guide covers the new **Discovery (no-basket)** pipeline that runs in parallel with the existing affiliate pipeline.

**Strategy:** mix discovery posts (aesthetic, no `#ad`, no basket) with affiliate posts (basketed, conversion-focused) at a ~1:2 ratio. Discovery posts feed the general FYP algorithm and build account authority; affiliate posts convert.

---

## 1. Git operations (work laptop)

- [ ] Wait for commit + push from the work laptop (Claude will handle)

## 2. Personal laptop — pull & environment

- [ ] `git pull` on personal laptop
- [ ] `cd tiktok-affiliate-ai && source venv/Scripts/activate`
- [ ] `pip install -r requirements.txt` — adds `gspread`; other deps unchanged
- [ ] `cd ai-frontend && npm install` — no new deps, safe to re-run
- [ ] Confirm `.env` still has `REPLICATE_API_TOKEN` (needed for nano-banana + Wan 2.2 Fast)

### Download Discovery BGM tracks (mood buckets)

The Discovery pipeline auto-picks BGM by product type for audio/visual coherence. The existing `happy-ukulele.mp3` stays for Affiliate posts; 3 new tracks need to be dropped into `assets/music/`. All free on [Pixabay Music](https://pixabay.com/music/) (CC0, no attribution, commercial OK). 30s+ each, under 5MB.

- [ ] Search "cinematic ambient" → save as `assets/music/cinematic-ambient.mp3` (die-cast + action figures)
- [ ] Search "lofi piano soft" → save as `assets/music/soft-lofi.mp3` (plushies)
- [ ] Search "lofi beats chill" → save as `assets/music/lofi-beats.mp3` (building blocks)
- [ ] Verify filenames match exactly — the pipeline looks these up by exact name in [core/bgm.py](core/bgm.py)

Mapping (auto, no UI):

| Product type | BGM mood key | File |
|---|---|---|
| die-cast | cinematic | cinematic-ambient.mp3 |
| action-figure | cinematic | cinematic-ambient.mp3 |
| plushie | soft | soft-lofi.mp3 |
| building-blocks | lofi | lofi-beats.mp3 |
| (unknown) | cinematic | cinematic-ambient.mp3 |

## 3. Smoke-test the cinematic pipeline (~$1.44 total)

- [ ] Start backend: `uvicorn api:app --reload`
- [ ] Start frontend (separate terminal): `cd ai-frontend && npm run dev`
- [ ] Open `http://localhost:3000`
- [ ] Click **Discovery Post** tile, upload a **die-cast** photo, generate — verify the 4 scenes look like a car bucket (mahogany desk, glass shelf, asphalt diorama, etc.)
- [ ] Repeat with a **plushie** photo → verify cozy bedroom / fairy lights / knitted blanket vibe
- [ ] Repeat with an **action figure** → verify collector shelf / display cabinet / gaming desk vibe
- [ ] Repeat with a **building-blocks** photo → verify workbench / Lego Store aesthetic vibe
- [ ] Open the history page → click the **Discovery** filter pill → confirm all 4 show up with purple "Discovery Post" badge

## 4. Verify caption correctness

Expand each Discovery result in the history view and confirm the caption:
- [ ] Contains **NO** `#ad`, `#sponsored`, `#TikTokShopPH`
- [ ] Contains **NO** `Comment X para sa link`, `basket`, `tap`, `shop` language
- [ ] Contains `#AIgenerated`
- [ ] Contains 1-2 category hashtags (e.g. `#PlushiePH`, `#DiecastPH`, `#AnimePH`, `#BuildingBlocks`)
- [ ] Ends with an engagement question

## 5. Update the 30-Day Google Sheet

Parameters locked:
- **Ratio:** 1 Affiliate + 2 Discovery per day (1:2)
- **Time-slot assignment:** 12 PM + 6 PM = Discovery, 9 PM = Affiliate
- **Blank captions:** Yes — Discovery rows get H (Caption) + I (First Comment) blanked so pipeline regenerates them
- **Column G:** new `Post_Style` column (between Status and Views) with values `Affiliate` or `Discovery`

Run the script from the project root on your personal laptop. **Docker is the recommended path** — matches the rest of your stack.

### Docker (recommended)
```bash
# One-time: rebuild backend image to pick up gspread dep (~2 min)
docker compose build backend

# Dry-run (prints planned changes + writes CSV backup to ./scripts/backups/)
docker compose run --rm \
  -v "$(pwd)/scripts/backups:/app/scripts/backups" \
  backend python scripts/update_30day_plan.py

# Review dry-run output + backup CSV, then apply
docker compose run --rm \
  -v "$(pwd)/scripts/backups:/app/scripts/backups" \
  backend python scripts/update_30day_plan.py --apply
```

The volume mount keeps the timestamped CSV backups on your host so you can restore from them.

### Native Python (alternative)
```bash
source venv/Scripts/activate
pip install gspread  # one-time; gspread was added to requirements.txt
python scripts/update_30day_plan.py              # dry-run
python scripts/update_30day_plan.py --apply      # apply
```

What it does:
- Skips any row with Status = "Posted" (untouched)
- Writes "Post_Style" header to G1
- Tags each remaining row's column G based on time slot
- Blanks H + I on Discovery rows so they regenerate via `discovery_copywriter`
- Saves a timestamped CSV backup to `scripts/backups/` before every run (dry-run and apply)

Restore from backup if anything goes sideways — the CSV has the exact pre-change state.

## 6. (Optional) Upgrade the `tiktokfirstcomment` skill

- [ ] Teach `.claude/skills/tiktokfirstcomment/SKILL.md` to check the new Post Type column and generate **engagement-only** first comments (no "Comment X for link") for Discovery rows. Affiliate rows keep the existing CTA-based logic.

## 7. Cost + throughput expectations

Both pipelines now support a **Free video mode** (Ken Burns pan on static scenes) and a **Premium** mode (AI-animated motion). Free is the default for both.

| Pipeline | Mode | Cost/post | Notes |
|---|---|---|---|
| Discovery | Free (default) | ~$0.18 | nano-banana scenes + Ken Burns + mood BGM |
| Discovery | Premium | ~$0.38 | + Wan 2.2 Fast motion (marginal FYP gain) |
| Affiliate | Free (default) | ~$0.49 | Kontext scenes + Ken Burns + voiceover + captions |
| Affiliate | Premium | ~$1.67 | + Wan 2.5 I2V motion |

### Monthly totals (30-day plan, 2:1 Discovery:Affiliate ratio)

| Strategy | Math | **Monthly** |
|---|---|---|
| **Both Free (recommended)** | 60 × $0.18 + 30 × $0.49 | **$25.50** |
| Discovery Free + Affiliate Premium | 60 × $0.18 + 30 × $1.67 | $60.90 |
| Both Premium | 60 × $0.38 + 30 × $1.67 | $73.00 |
| All-Affiliate Premium (old pattern) | 90 × $1.67 | $150.30 |

Free mode keeps the whole 30-day campaign under **~$26/month**. That's a 5x savings vs the old all-Premium pattern, and TikTok's FYP algorithm does not penalize still-image Ken Burns content — the aesthetic reads as photo-reel/Netflix-style, which actually outperforms over-animated AI video on retention.

---

## What changed in the codebase

### New files
- `agents/discovery_copywriter.py` — caption-only generator for no-basket posts
- `core/cinematic_scenes.py` — nano-banana wrapper with product-type-aware `SCENE_BUCKETS`
- `core/cinematic_video.py` — Wan 2.2 Fast wrapper with randomized `MOTION_POOL`

### Modified files
- `workflows/ad_pipeline.py` — added `_detect_product_type()` helper and `_run_cinematic_pipeline()` branch; `run_pipeline()` now branches on `input_data["style"]`
- `api.py` — `AdRequest` now accepts `style: "affiliate" | "cinematic"` (default affiliate), allowlist-validated
- `ai-frontend/app/page.tsx` — two-button Post Type selector at top of form, hides voiceover/BGM/AI-video controls for cinematic, sends `style` in POST body
- `ai-frontend/app/history/page.tsx` — All / Affiliate / Discovery filter pills
- `ai-frontend/app/components/AdCard.tsx` — three-way compliance badge (Compliant / Discovery / Issues), hides Script/Scene Plan/QA sections for Discovery posts

### Scene + motion variety math

- **Scene buckets:** 4 product types × 6 scenes each = 24 scenes total. `C(6,4) = 15` unique scene combinations per product type — 60 Discovery videos over 30 days will effectively never repeat within a category.
- **Motion pool:** 6 camera moves. `C(6,4) = 15` unique motion combinations per video.
- **Combined variety per product type:** 15 × 15 = 225 distinct scene+motion combinations before repeats.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `style must be 'affiliate' or 'cinematic'` 400 error | Frontend sent something other than allowlist values. Check you're on latest pull. |
| Cinematic generate fails immediately with "requires at least one product_image_url" | Discovery mode requires 1 product photo — upload one before clicking Generate. |
| Scene images all look the same across runs | The bucket was too small. Expand the relevant `SCENE_BUCKETS[<type>]` list in `core/cinematic_scenes.py`. |
| Discovery caption has `#ad` in it | Server-side filter should strip it. If it slips through, update the `forbidden` set in `workflows/ad_pipeline.py::_run_cinematic_pipeline()`. |
| Wan 2.2 Fast returns 404 | Model slug drifted on Replicate. Check `replicate.com/wan-video` for the current i2v-fast variant and update `WAN_URL` in `core/cinematic_video.py`. |
| Product type detected wrong (e.g. plushie classified as die-cast) | Add the missing keyword to `_detect_product_type()` in `workflows/ad_pipeline.py`. |

---

## Next steps after validation

1. Post 3-5 Discovery videos over 48 hours and compare views against recent basketed posts (current baseline: 3-8 views on basketed posts vs 336/387 pre-basket)
2. If Discovery posts pull 100+ views consistently, the FYP algorithm is routing them correctly — start scaling to the full 2:1 ratio across the 30-day plan
3. Watch account "Not interested" rate in TikTok analytics — if it stays low, the balance is working
