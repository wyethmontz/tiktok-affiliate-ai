# CLAUDE.md

This file guides Claude Code when working in this repository.
Read it fully before making any changes.

---

## Project

**TikTok Affiliate AI** — AI pipeline that generates TikTok-compliant affiliate ads from a product brief.
Produces strategy, script, scenes, images, voiceover, and video — fully ready to post.

**Stack:** Python 3.11 FastAPI backend + Next.js 16 TypeScript frontend, both containerized.
**Database:** Supabase (PostgreSQL). **Auth:** Supabase Auth (JWT).
**Deployment:** EC2 (Ubuntu 22.04) running docker-compose behind Cloudflare tunnels.

---

## Quick Start

```bash
# Backend
source venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
uvicorn api:app --reload        # http://localhost:8000

# Frontend
cd ai-frontend && npm install && npm run dev   # http://localhost:3000

# Both via Docker
docker-compose up --build
```

**Environment files (never commit values):**
- Backend: `.env` (see `.env.example`)
- Frontend: `ai-frontend/.env.local` (see `ai-frontend/.env.example`)

---

## Architecture

```
User Input (product name + photo/video)
   → Optimizer        (reads top past ads from Supabase, finds patterns)
   → Strategist       (hook, angle, positioning, audience detection)
   → Copywriter       (Tagalog TikTok script + CTA + #ad)
   → Creative Director (4 visual scenes, 9:16 format)
   → Compliance Agent  (policy check, auto-rewrites up to 4x)
   → [MODE A] Kontext Scenes (Flux Kontext Pro) → Video Gen (Wan 2.5 I2V)
   → [MODE B] User Video Clips (skip gen, use raw recordings)
   → [MODE C] Image Gen (Flux Schnell) → Video Gen (Wan 2.5 I2V)
   → Voiceover        (ElevenLabs TTS, Filipina voice)
   → Video Assembler  (FFmpeg: clips + voiceover + BGM + captions → MP4)
   → Supabase         (save full ad record)
   → Frontend         (display with video player + caption)
```

### Key Files
| File | Purpose |
|---|---|
| `api.py` | FastAPI routes (all endpoints) |
| `core/llm.py` | Claude API wrapper — extend this, don't bypass it |
| `core/db.py` | Supabase client + `save_ad()` |
| `core/job_store.py` | In-memory job tracking (swappable to Redis) |
| `core/auth.py` | JWT auth middleware (use as `Depends`) |
| `workflows/ad_pipeline.py` | 13-step pipeline orchestrator |
| `agents/` | 8 AI agents (one concern each) |

### API Endpoints
| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/generate-ad` | ✅ | Start pipeline (returns `job_id`) |
| `GET` | `/jobs/{job_id}` | ✅ | Poll status + progress |
| `GET` | `/ads` | ✅ | List ads (`?search=` filter) |
| `GET` | `/ads/{ad_id}` | ✅ | Single ad |
| `GET` | `/analytics/summary` | ✅ | Dashboard stats |
| `GET` | `/analytics/insights` | ✅ | AI insights |
| `GET` | `/health` | ❌ | Health check (used by CI smoke test) |

---

## Claude Token Optimization

**This is critical.** This app calls Claude 8+ times per ad. Wasteful usage compounds across every generation.

### 1. Always Use Prompt Caching for System Prompts

Every agent has a large, static system prompt (TikTok policy, persona, rules). Cache it.

```python
# BAD — system prompt re-tokenized every call
response = client.messages.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": system_prompt + "\n\n" + user_prompt}]
)

# GOOD — system prompt cached server-side (saves 60-80% tokens on repeat calls)
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": SYSTEM_PROMPT,           # large static context here
            "cache_control": {"type": "ephemeral"}
        }
    ],
    messages=[{"role": "user", "content": user_prompt}]
)
```

Cache TTL is 5 minutes. Cache is reused if the system prompt is identical byte-for-byte.

### 2. Right-Size Model per Task

| Task | Model | Why |
|---|---|---|
| Strategy, copywriting, compliance rewrite | `claude-sonnet-4-6` | Needs creativity + context |
| QA scoring, simple classification | `claude-haiku-4-5-20251001` | Cheap, fast, sufficient |
| Optimizer (pattern extraction from data) | `claude-sonnet-4-6` | Complex reasoning |
| Routing / intent detection | `claude-haiku-4-5-20251001` | 10x cheaper |

### 3. Set `max_tokens` Per Task

```python
# BAD — 1024 for everything wastes budget on short outputs
call_claude(prompt)  # current code: always max_tokens=1024

# GOOD — match to expected output size
client.messages.create(model=..., max_tokens=200, ...)   # QA score + 1-sentence reason
client.messages.create(model=..., max_tokens=800, ...)   # full ad script
client.messages.create(model=..., max_tokens=400, ...)   # 4 scene descriptions
```

### 4. Use Structured Output (Tool Use)

Forces Claude to return JSON directly — no parsing errors, fewer tokens wasted on prose.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    tools=[{
        "name": "output_strategy",
        "description": "Return the ad strategy",
        "input_schema": {
            "type": "object",
            "properties": {
                "hook": {"type": "string"},
                "angle": {"type": "string"},
                "format": {"type": "string", "enum": ["GRWM", "POV", "unboxing", "tutorial"]},
                "audience": {"type": "string"}
            },
            "required": ["hook", "angle", "format", "audience"]
        }
    }],
    tool_choice={"type": "tool", "name": "output_strategy"},
    messages=[{"role": "user", "content": prompt}]
)
result = response.content[0].input  # already a dict, no json.loads() needed
```

### 5. Don't Repeat Context Across Agents

Pass only what each agent needs. Don't dump the full ad record into every prompt.

```python
# BAD — sends everything to every agent
prompt = f"Here is the full ad record: {json.dumps(full_ad_dict)}\n\nNow do X"

# GOOD — send only relevant fields
prompt = f"Script: {script}\nProduct: {product}\n\nDo X"
```

### 6. Batch Supabase Reads Before Pipeline

The optimizer already reads past ads from Supabase. Do this once, pass the results downstream.
Never query Supabase inside a Claude prompt loop.

### 7. Reuse the Client Instance

`core/llm.py` creates one `Anthropic()` client at module level. Keep it that way.
Never create a new client per request — it opens a new HTTP connection every time.

---

## Python / FastAPI Standards

### Type Hints — Always
```python
# BAD
def call_claude(prompt):
    ...

# GOOD
def call_claude(prompt: str) -> str:
    ...
```

All function signatures, Pydantic models, and return types must have type annotations.
Use `from __future__ import annotations` at the top of each file.

### Pydantic v2 Models
```python
# BAD — no validation, allows empty strings
class AdRequest(BaseModel):
    product: str

# GOOD — validated at the boundary
class AdRequest(BaseModel):
    product: str = Field(..., min_length=1, max_length=200, strip_whitespace=True)
    audience: str | None = Field(None, max_length=100)

    @field_validator("product")
    @classmethod
    def no_html(cls, v: str) -> str:
        if "<" in v or ">" in v:
            raise ValueError("HTML not allowed")
        return v
```

- Validate at the API boundary — trust internal function calls
- Use `Field(...)` not `Field(default=...)` for required fields
- Use `model_config = ConfigDict(str_strip_whitespace=True)` on models that accept user text

### Route Design
```python
# BAD — business logic in route, no auth, no error handling
@app.post("/generate-ad")
async def generate(req: AdRequest):
    result = run_pipeline(req.product)
    return result

# GOOD — thin route, auth dependency, background task, proper response
@app.post("/generate-ad", status_code=202)
@limiter.limit("5/minute")
async def generate(
    req: AdRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    user=Depends(get_current_user),
):
    job_id = str(uuid.uuid4())
    background_tasks.add_task(run_pipeline, job_id, req, user.id)
    return {"job_id": job_id, "status": "queued"}
```

### Error Handling
```python
# BAD — leaks internal error messages
except Exception as e:
    return {"error": str(e)}

# GOOD — use HTTPException, log internally
except ReplicateError as e:
    logger.error("Replicate API failed: %s", e)
    raise HTTPException(status_code=502, detail="Image generation service unavailable")
```

- Raise `HTTPException` in routes, never return raw exception strings
- Log with `logging` (not `print`) — logs surface in CloudWatch
- Use specific exception types, not bare `except Exception`

### Async
- Use `async def` for all route handlers and any function that does I/O (HTTP calls, Supabase, file I/O)
- Use `def` (sync) for pure computation (string building, data transformation)
- Never use `time.sleep()` in an async context — use `await asyncio.sleep()`

### Module Structure — One Concern Per File
```
agents/strategist.py   → only strategist logic
agents/copywriter.py   → only copywriter logic
core/llm.py            → only Claude API calls
core/db.py             → only database operations
```

Never import from `workflows/` inside `agents/` — that inverts the dependency.

---

## TypeScript / Next.js Standards

### TypeScript Config (Strict Mode)
`ai-frontend/tsconfig.json` must have:
```json
{
  "compilerOptions": {
    "strict": true,
    "noImplicitAny": true,
    "noUncheckedIndexedAccess": true
  }
}
```

### No `any`
```typescript
// BAD
const data: any = await response.json()

// GOOD — define the shape
interface AdResponse {
  job_id: string
  status: 'queued' | 'running' | 'done' | 'error'
}
const data: AdResponse = await response.json()
```

Use `unknown` when the type is truly unknown, then narrow with type guards.

### Server vs Client Components (App Router)
```typescript
// By default — server component (preferred)
// Can fetch data directly, no 'use client' needed
export default async function HistoryPage() {
  const ads = await fetchAds()   // runs on server, no API round-trip
  return <AdList ads={ads} />
}

// Only add 'use client' when you need: useState, useEffect, onClick, browser APIs
'use client'
export default function SearchBar({ onSearch }: { onSearch: (q: string) => void }) {
  const [query, setQuery] = useState('')
  ...
}
```

Rule: start server, add `'use client'` only when forced to.

### Data Fetching
```typescript
// BAD — client-side fetch with useEffect (extra round-trip, loading states)
useEffect(() => { fetch('/ads').then(r => r.json()).then(setAds) }, [])

// GOOD — async server component (zero loading state, no extra request)
export default async function Page() {
  const ads = await fetch(`${process.env.API_URL}/ads`, { next: { revalidate: 60 } })
  ...
}
```

### Tailwind
- Utility classes only — no inline `style={{}}` props
- Organize classes: layout → spacing → sizing → typography → color → state
- Extract repeated class strings to a `cn()` utility, not to a new CSS file

### API Client
- Use a typed API client in `lib/api.ts`, not raw `fetch` scattered across components
- Always handle errors — `response.ok` check before `.json()`
- Never expose `ANTHROPIC_API_KEY` or server-only secrets in `NEXT_PUBLIC_*` env vars

---

## Docker Standards

### Backend Dockerfile Rules
```dockerfile
# Pin exact version — never use `latest` or unversioned tags
FROM python:3.11.9-slim

# Install OS deps first (cached layer — rarely changes)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps before copying code (layer cache invalidates on requirements.txt change only)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code last (invalidates most often)
COPY . .

# Non-root user — never run containers as root
RUN useradd --no-create-home --uid 1001 appuser
USER appuser

# Health check — used by docker-compose and CI smoke tests
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

### Frontend Dockerfile Rules
```dockerfile
# Multi-stage: build stage is heavy (devDeps + Next.js compiler)
# Runtime stage is lean (only production output)
FROM node:20.19-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY
RUN npm run build

# Runtime stage — no devDeps, no source, no build tools
FROM node:20.19-alpine AS runtime
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public ./public
USER appuser
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -qO- http://localhost:3000 || exit 1
EXPOSE 3000
CMD ["node", "server.js"]
```

### .dockerignore (both services)
```
.git
.env
.env.local
node_modules
__pycache__
*.pyc
.pytest_cache
.mypy_cache
uploads/
*.log
```

### Rules
- Never put secrets in `ENV` instructions — pass at runtime via `env_file` or `--env`
- Never use `COPY . .` before installing deps — it breaks layer caching
- Always add `HEALTHCHECK` — CI smoke tests and docker-compose use it
- Multi-stage builds for any image with a build step (TypeScript, Go, etc.)

---

## GitHub Actions Standards

### Action Pinning
```yaml
# BAD — @latest can break silently when action updates
- uses: actions/checkout@latest
- uses: aws-actions/amazon-ecr-login@v1

# GOOD — pin to SHA for security, or at least @v4 major version
- uses: actions/checkout@v4
- uses: aws-actions/amazon-ecr-login@v2
```

### Every Job Needs a Timeout
```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 20    # prevents runaway jobs burning minutes
```

### Least-Privilege Permissions
```yaml
permissions:
  contents: read           # only what each job needs
  id-token: write          # for OIDC auth to AWS (better than long-lived keys)
```

### Dependency Caching
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}

- uses: actions/cache@v4
  with:
    path: ai-frontend/.next/cache
    key: ${{ runner.os }}-next-${{ hashFiles('ai-frontend/package-lock.json') }}
```

### Secrets
```yaml
# BAD — hardcoded in YAML
AWS_REGION: ap-southeast-1

# GOOD — secrets in GitHub Secrets, non-sensitive config in vars
AWS_REGION: ${{ vars.AWS_REGION }}
AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
```

Never echo secrets. If you must debug, use `::add-mask::${{ secrets.SOMETHING }}`.

---

## Terraform Standards

### Remote State (Required)
```hcl
# backend.tf — state in S3, lock in DynamoDB
terraform {
  backend "s3" {
    bucket         = "tiktok-ai-tf-state"
    key            = "prod/terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "tiktok-ai-tf-lock"
    encrypt        = true
  }
}
```

### Tag Every Resource
```hcl
locals {
  common_tags = {
    Project     = "tiktok-affiliate-ai"
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_instance" "app" {
  ...
  tags = merge(local.common_tags, { Name = "tiktok-ai-${var.environment}" })
}
```

### No Hardcoded Values
```hcl
# BAD
instance_type = "t3.medium"
region        = "ap-southeast-1"

# GOOD — in variables.tf
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}
```

### Workflow
```bash
terraform fmt        # format before every commit
terraform validate   # catch syntax errors
terraform plan -out=tfplan  # review before applying
terraform apply tfplan
```

Never run `terraform apply` without reviewing `terraform plan` output first.

---

## EC2 Operations

### Instance Details
| Field | Value |
|---|---|
| Instance ID | `i-07261f58c3758e95b` |
| Region | `ap-southeast-1` |
| Key pair name | `tiktok-ai-key` (file: `~/.ssh/tiktok-ai-key.pem`) |
| App path | `/opt/app/` |

### Secrets Manager
| Secret | ARN |
|---|---|
| `tiktok-ai/google-creds` | `arn:aws:secretsmanager:ap-southeast-1:449262240596:secret:tiktok-ai/google-creds-N747SK` |

To update a secret from a local file (confirmed working):

```powershell
aws secretsmanager put-secret-value `
  --secret-id tiktok-ai/google-creds `
  --secret-string file://"$env:USERPROFILE\tiktok-affiliate-ai\google-creds.json" `
  --region ap-southeast-1
```

### Always Look Up the Current IP First

The instance has **no Elastic IP**. The public IP changes every time it is stopped and started. Never rely on a remembered IP — always fetch it fresh:

```powershell
aws ec2 describe-instances `
  --region ap-southeast-1 `
  --instance-ids i-07261f58c3758e95b `
  --query "Reservations[0].Instances[0].PublicIpAddress" `
  --output text
```

Then SSH using the result:

```powershell
ssh -i "$env:USERPROFILE\.ssh\tiktok-ai-key.pem" ubuntu@<ip-from-above>
```

### All Server Commands Require SSH First

This project is developed on **Windows**. `/opt/app/` is a Linux path on the EC2 server.
Commands like `sudo nano /opt/app/.env` must be run **inside an SSH session**, not in local PowerShell.

```
# Wrong — running on local Windows machine
sudo nano /opt/app/.env         ← Linux command, wrong machine

# Right — SSH in first, then run the command
ssh -i "~/.ssh/tiktok-ai-key.pem" ubuntu@<ec2-ip>
ubuntu@ec2:~$ sudo nano /opt/app/.env
```

To push a local file to the server without SSHing:

```powershell
scp -i "$env:USERPROFILE\.ssh\tiktok-ai-key.pem" .env ubuntu@<ec2-ip>:/opt/app/.env
```

### AWS CLI in PowerShell — Use `file://` for File Contents

PowerShell's `(Get-Content ...)` command substitution breaks AWS CLI argument parsing when the file contains special characters (JSON keys, PEM headers, etc.).

```powershell
# BAD — file contents get parsed as CLI flags
aws secretsmanager put-secret-value `
  --secret-string (Get-Content "$env:USERPROFILE\tiktok-affiliate-ai\google-creds.json" -Raw)

# GOOD — let AWS CLI read the file directly
aws secretsmanager put-secret-value `
  --secret-id tiktok-ai/google-creds `
  --secret-string file://"$env:USERPROFILE\tiktok-affiliate-ai\google-creds.json" `
  --region ap-southeast-1
```

The `file://` prefix works for any `--secret-string`, `--policy-document`, `--assume-role-policy-document`, etc.

---

## DevSecOps Standards

### Trivy Image Scanning (CI — blocks on CRITICAL)
```yaml
- name: Scan image for vulnerabilities
  uses: aquasecurity/trivy-action@0.28.0
  with:
    image-ref: ${{ env.IMAGE_URI }}
    format: table
    exit-code: 1            # fails CI
    severity: CRITICAL      # only block on critical
    ignore-unfixed: true    # skip CVEs with no fix yet
```

### Bandit SAST (Python security)
```yaml
- name: Python security scan (Bandit)
  run: |
    pip install bandit
    bandit -r . -x ./tests,./venv --severity-level medium -f json -o bandit-report.json || true
    bandit -r . -x ./tests,./venv --severity-level high    # fail on HIGH+
```

### Dependabot
`.github/dependabot.yml` must exist and cover both ecosystems:
```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
  - package-ecosystem: npm
    directory: /ai-frontend
    schedule:
      interval: weekly
```

### Secret Scanning
- Enable in GitHub repo → Settings → Security → Secret scanning
- Enable "Push protection" so secrets are blocked before they land in git

### Container Hardening Checklist
- [ ] Non-root user (`USER appuser`)
- [ ] No `--privileged` in docker-compose
- [ ] No secrets in `ENV` or `ARG` (except `NEXT_PUBLIC_*` build args)
- [ ] Minimal base image (slim/alpine variants)
- [ ] `HEALTHCHECK` defined

---

## Security Checklist (per PR)

1. **Rate limits** — every public endpoint has `@limiter.limit()`
2. **Input validation** — all user fields have `max_length`, `min_length`, type constraints
3. **Auth** — sensitive routes use `Depends(get_current_user)`
4. **CORS** — `ALLOWED_ORIGINS` env var set in production (never `*`)
5. **Secrets** — no `.env`, credentials, or keys committed to git
6. **Logging** — no API keys or user data in log output
7. **Errors** — `HTTPException` only, never raw exception strings to clients
8. **HTTPS** — Cloudflare tunnel provides HTTPS; never serve over plain HTTP in prod

---

## Database (Supabase)

**Table:** `ads`

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key |
| `product` | text | Product name |
| `audience` | text | |
| `platform` | text | |
| `goal` | text | |
| `hook` | text | |
| `angle` | text | |
| `positioning` | text | |
| `copy` | text | Full ad script |
| `creative` | jsonb | Scene descriptions |
| `qa_score` | text | e.g. "8/10" |
| `qa_score_numeric` | int | 1–10 |
| `media` | text | |
| `images` | text | Comma-separated URLs |
| `voiceover_url` | text | |
| `compliance_status` | text | |
| `tiktok_caption` | text | Ready-to-paste caption |
| `created_at` | timestamptz | |

---

## TikTok Compliance (Enforced by Compliance Agent)

1. No fabricated claims (prices, stats, testimonials)
2. `#ad` or `#sponsored` in every CTA
3. `#AIgenerated` hashtag + AIGC label reminder in every output
4. No fake urgency/scarcity unless verified
5. No health/beauty claims without evidence
6. Claims match only what the user provided — nothing invented
7. No real public figures
8. No fake "in-hand" product usage

**AIGC Labeling Required on Post:**
Enable TikTok's in-app toggle: Post Settings → More options → AI-generated content ON

---

## Pre-commit Checklist

Run these before every commit to catch CI failures locally:

```bash
# Backend
source venv/Scripts/activate
python -m ruff check .          # must be zero errors before committing

# Frontend
cd ai-frontend
npm run lint                    # must be zero errors before committing
npm test -- --ci --passWithNoTests
```

### Rules that have caused CI failures — don't repeat these

**Python**
- Never call `create_client()` or any external service at module level — use lazy init (`if URL and KEY else None`) so imports don't crash when env vars are absent (tests mock at the attribute level, not import-time)
- Every Pydantic field that accepts user text must have both `min_length` and `max_length` — missing `min_length=1` on `product` let empty strings through validation

**Frontend**
- Never use `require()` in `.js` files — the ESLint rule `@typescript-eslint/no-require-imports` blocks it; use ESM imports or add the file to `globalIgnores` in `eslint.config.mjs`
- Don't call `setState` inside `useEffect` for one-time initialization from `localStorage` — use a lazy `useState` initializer: `useState(() => { ... })` instead
- When writing Jest tests that use `jest.useFakeTimers()` with `@testing-library/user-event` v14, always use `userEvent.setup({ advanceTimers: jest.advanceTimersByTime.bind(jest) })` — calling `userEvent.type()` with global fake timers active causes the test to hang indefinitely
- After adding any package to `package.json`, run `npm install` and commit the updated `package-lock.json` — `npm ci` in CI fails if the lock file is out of sync

**CI / GitHub Actions**
- Workflow `on: push/pull_request` branch filters must match the repo's actual default branch (`master`, not `main`) — mismatched branch name silently skips CI on all PRs
- Always verify action versions exist and use the correct tag format — trivy-action tags use a `v` prefix: `aquasecurity/trivy-action@v0.36.0`, not `0.36.0`; check tags via `gh api repos/<owner>/<repo>/tags --jq '.[].name' | head -5`

---

## What NOT to Do

- Don't bypass `core/llm.py` — always go through the wrapper so caching and model selection stay centralized
- Don't add `print()` — use `import logging; logger = logging.getLogger(__name__)`
- Don't commit `.env`, `google-creds.json`, or any file with real API keys
- Don't use `model="claude-sonnet-4-6"` for QA scoring — use Haiku
- Don't set `max_tokens=1024` for every Claude call — match it to expected output length
- Don't skip `terraform plan` before `terraform apply`
- Don't run containers as root
- Don't use `any` in TypeScript

---

## Deploy Guide Maintenance

`DEPLOY_GUIDE.md` is the single source of truth for deploying this project from scratch.
It must stay accurate and error-free at all times.

**Rule: every error encountered while following the guide must be fixed in the guide immediately.**

When a user hits an error during deployment:
1. Identify which step in `DEPLOY_GUIDE.md` caused or failed to prevent the error
2. Update that step so a user following the guide fresh would never hit the same error
3. If the error reveals a missing warning, add a callout at the exact point where the user would go wrong
4. If the error reveals a wrong or incomplete command, replace it with the confirmed-working version
5. If the error is caused by an omission in `.gitignore` or another config file, fix that file too

Do not just fix the immediate problem in the terminal — always trace it back to the guide and patch the root cause there.
