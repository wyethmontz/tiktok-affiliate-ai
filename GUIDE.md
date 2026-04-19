# TikTok Affiliate AI — Complete Guide

## Part 1: Setting Up Your TikTok Account

### Priority Checklist (do these first, in order)

Before your first post, you only need 3 things done:

1. **Username** — niche-related, not generic
   - Good: `@toyfinds.ph`, `@kuya.toys`, `@pinay.deals`
   - Bad: `@user29384738`, `@john123`
2. **Bio** — short, under 80 characters
   - Example: `🚗 Toy finds sa TikTok Shop 🛒 Para sa bata at collectors 👇 Watch my reviews!`
3. **Profile photo** — use a product image from your pipeline or your face

### Full Video Creation Process (Step by Step)

**Step 1: Find affiliate product (MOBILE)**
- Open TikTok app → Profile → Creator Tools (or TikTok Studio) → **Affiliate**
- Tap **Find Products** or **Marketplace**
- Filters:
  - Category: Toys & Hobbies
  - Commission rate: **15% and up**
  - 4+ stars, 100+ sold
- Tap a product you want to promote
- **Long-press the main product image → Save image** (or copy image URL)
- Note the product name too

**Best product photo for AI:**
- Single product, not multiple items
- Clean background (white or plain)
- Well-lit, sharp focus, not blurry
- Shows the full product (not cropped)

**Alternative sources:**
- Shopee/Lazada listings (single-product images, white bg)
- Your own photo on a white table

**Step 2: Generate the video (PC — localhost:3000)**
1. Make sure Docker is running (`docker-compose up`)
2. Open `http://localhost:3000`
3. Type the product name — be specific (5-8 words, e.g., `Cute Tanjiro Demon Slayer Action Figure Poseable`)
4. Click **"+ Add product images"**
5. Drag & drop the saved image OR paste the image URL
6. Click **"Generate TikTok Ad"** (~3 minutes)
7. Review the result:
   - Compliance badge should be **green** (TikTok Compliant)
   - Watch the video — check the images look good
   - If scenes look bad, click **"Regenerate Video"** (keeps script, redoes visuals only)
8. Click **"Download MP4"** to save
9. Click **"Copy Caption"** to copy the caption

**Step 3: Transfer video to phone**
- **Fastest:** Upload MP4 to Google Drive → open Drive on phone → download
- **Alternative:** Send MP4 to yourself on Telegram/Messenger → save to phone

**Step 4: Post to TikTok (MOBILE — required for affiliate link)**

Must use mobile app to add the yellow basket (affiliate product link). PC Web Studio cannot add product links.

1. Tap **+** → **Upload** → select the MP4
2. **Description:** Paste the TikTok Caption from the app (click "Copy Caption") — only 5 hashtags
3. **Add product link (yellow basket):**
   - Tap **Add link** or basket icon
   - Search for the SAME product you picked in Step 1 (use the "TikTok Name (30 char)" column from the sheet)
   - Select it → basket link appears in video
4. **Location:** Leave blank
5. **When to post:** **Schedule** at 12 PM / 6 PM / 9 PM PHT
6. **Who can watch:** Everyone

**Disclosure and ads settings (with affiliate basket):**
| Setting | Toggle |
|---------|--------|
| Disclose commercial content | **ON** |
| Your brand | **UNCHECKED** (you're not promoting your own business) |
| Branded content | **CHECKED** (you're promoting seller's product) |
| Ad authorization | OFF |
| Only show as ads | OFF |
| AI-generated content | **ON** (REQUIRED) |

**Allow users to:**
| Setting | Toggle |
|---------|--------|
| Allow comments | **ON** (engagement = algorithm boost) |
| Allow reuse of content (Duet/Stitch) | **ON** (free exposure) |
| Allow AI to remix content | **ON** (more reach) |

**More options:**
| Setting | Toggle |
|---------|--------|
| Allow visual search | **ON** (people find products through search) |
| Allow high-quality uploads | **ON** |
| Post as template | **ON** (others remix = more views) |
| Save to device | **OFF** (already have MP4) |
| Save posts with watermark | **OFF** |
| Audience controls (18+) | **OFF** (toys aren't 18+) |

**Content checks:**
- Music copyright check: should pass (we use royalty-free Pixabay)
- Content check lite: should pass

Tap **Schedule** (or **Post**)

**Step 5: After posting**
- Pin a comment: "Tap the yellow basket below! 👇"
- Reply to every comment within the first hour
- Don't delete even if low views
- Update Google Sheet (Status = Posted)
- Generate next video for next time slot

---

### Mobile Access (access the tool from your phone)

Avoid the phone→PC→phone transfer hassle by running the tool from your phone browser using Cloudflare Tunnel (free).

**One-time setup — Install cloudflared:**

1. Open https://github.com/cloudflare/cloudflared/releases/latest
2. Scroll to **Assets**, download **`cloudflared-windows-amd64.exe`**
3. Open your Downloads folder
4. Right-click the file → **Rename** → change to `cloudflared.exe`
5. Open **This PC** → navigate to `C:\Windows\System32\`
6. Drag `cloudflared.exe` into `System32` (admin prompt → click Continue)
7. Verify install — open new PowerShell:
   ```powershell
   cloudflared --version
   ```
   You should see a version number like `2025.x.x`

**One-time setup — Allow PowerShell scripts:**

If PowerShell blocks the tunnel script, run this once:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Daily usage:**
1. On your PC, run:
   ```powershell
   cd c:\Users\wyethmontana\tiktok-affiliate-ai
   .\scripts\start_tunnel.ps1
   ```
2. Script auto-starts both tunnels (frontend + backend) and updates the frontend config
3. Copy the **FRONTEND URL** it prints (e.g., `https://random-name.trycloudflare.com`)
4. Rebuild Docker once: `docker-compose up --build`
5. Open the frontend URL on your phone browser

**Now you can:**
- Find product on TikTok mobile → long-press image → Save
- Open tool in phone browser → drag-drop or paste image
- Generate video on pipeline
- Video saves directly to phone
- Upload to TikTok on same phone → link yellow basket
- Never touch PC during posting

**Catch:** URLs change every time you restart the tunnel. Just rerun the script + rebuild Docker.

**Keep the script window open** — closing it kills the tunnels.

**Then post your first video at the right time:**

| Time (PHT) | Priority |
|------------|----------|
| **6-9 PM** | Best — peak Filipino TikTok hours |
| 12-1 PM | Good — lunch break scroll |
| 7-8 AM | Good — morning scroll |
| 10-11 PM | OK — late night |

Everything else (business account, affiliate links) can happen after. The algorithm starts learning from post #1.

### 1.1 Create Your Account

1. Download TikTok from App Store or Google Play
2. Sign up with **email** (not phone — easier to recover)
3. Set username, bio, and profile photo (see checklist above)
4. Post your first video

### 1.2 Switch to Business Account (do later, not required to post)

1. Profile > **Settings and privacy** > **Account** > **Switch to Business Account** (or **Account type**)
2. Pick category: **Retail** or **Online Shopping**
3. This unlocks analytics and the ability to add links
4. Free, instant, no verification needed

**Note:** If you can't find the option, skip it. It's not required to post or make sales.

### 1.3 Join TikTok Shop Affiliate Program (do after building audience)

1. Go to **TikTok Seller Center** (seller-ph.tiktok.com) or search "TikTok Shop Affiliate" in your browser
2. Click **Sign up as Affiliate/Creator**
3. Requirements:
   - 1,000+ followers (for some features)
   - 18+ years old
   - Account in good standing
4. Once approved, you can browse the TikTok Shop marketplace and get affiliate links
5. You earn **commission (5-20%)** on every sale through your link

**Note:** You can start posting content immediately while waiting for affiliate approval. Build your audience first — don't wait for approval to start posting.

### 1.4 Account Settings for Compliance

**Privacy settings:**
- Profile > Settings > Privacy > set account to **Public** (required for reach)

**Content settings:**
- Do NOT turn on "Private account"
- Enable comments (engagement helps algorithm)
- Allow Duets and Stitches (more exposure)

**Creator tools:**
- Profile > Creator tools > turn on **Analytics** (track what works)

---

## Part 2: Understanding TikTok Rules (Don't Get Banned)

### 2.1 AIGC (AI-Generated Content) Rules

TikTok requires disclosure for ALL AI-generated content. Our pipeline handles this automatically, but you must also:

**REQUIRED on every AI-generated post:**
1. Enable the **AIGC toggle**: Post Settings > More options (...) > "AI-generated content" > ON
2. Include **#AIgenerated** in your caption (our pipeline adds this)
3. Include **#ad** for affiliate content (our pipeline adds this)

**What TikTok considers AIGC:**
- AI-generated images (Flux Kontext scenes)
- AI voiceover (ElevenLabs)
- AI-generated video (Wan 2.5 I2V)
- AI-written scripts (Claude)

**Labeling does NOT hurt your reach.** TikTok has confirmed this publicly. Not labeling CAN get you banned.

### 2.2 Affiliate Disclosure Rules

**Required by law (FTC) and TikTok policy:**
- Every post promoting an affiliate product must include #ad or #sponsored
- Must be visible (not hidden at the end of 50 hashtags)
- Our pipeline puts #ad at the front of every caption

### 2.3 Content That Gets You Banned

| Violation | Example | Consequence |
|-----------|---------|-------------|
| No AIGC label | Posting AI video without toggle | Warning → ban |
| Fake claims | "Cures acne", "Lost 10kg in a week" | Content removed |
| Fake urgency | "Only 3 left!" (when you don't know) | Content removed |
| Fake endorsements | "Doctors recommend this" | Content removed |
| No #ad disclosure | Promoting affiliate without #ad | Content removed, legal risk |
| Spam posting | 10+ identical videos in an hour | Shadow ban |
| Using minors | AI-generated children | Permanent ban |
| Public figures | AI-generated celebrity endorsement | Permanent ban |

### 2.4 Safe Content Practices

**Always safe:**
- Showing the real product
- Saying "I found this on TikTok Shop"
- Describing what the product looks like
- Sharing your genuine opinion/excitement
- Using #ad and #AIgenerated

**Never safe:**
- Inventing prices, reviews, or statistics
- Claiming health/medical benefits
- Saying "selling out fast" without proof
- Pretending AI content is real footage
- Using real people's faces/voices without permission

---

## Part 3: Creating Content with the AI Pipeline

### 3.1 Find a Product

**Where to find products:**
- TikTok Shop Marketplace — browse trending products
- Shopee/Lazada — look at bestsellers
- Pick products with existing demand (toys, beauty, gadgets, home)

**Good products for TikTok:**
- Under $20 / under 1000 PHP (impulse buy range)
- Visually interesting (looks good on camera)
- Solves a problem or triggers "I want that"
- Already trending on TikTok

### 3.2 Get Your Product Photo

**Best product photo for AI scene generation:**
- Clean, single product on plain background
- Well-lit, sharp focus
- Shows the full product (not cropped)
- Use the listing photo from Shopee/TikTok Shop or take one yourself

**How to get the photo:**
- Screenshot from TikTok Shop listing
- Save from Shopee/Lazada product page
- Take your own photo on a white table
- Google Drive link (make sure sharing is set to "Anyone with the link")

### 3.3 Generate the Ad

1. Open the app at `http://localhost:3000`
2. Type the product name — be specific:
   - Good: `Lightning McQueen Sky Blue Custom Edition Toy Car`
   - Bad: `car toy`
3. Click **"+ Add product images"**
4. Drop 1 product photo or paste a Google Drive / image link
5. Click **"Generate TikTok Ad"**
6. Wait ~2-3 minutes

**What the AI does automatically:**
```
Your product photo
  → Picks the best target audience
  → Picks the best marketing goal
  → Writes a 15-second Tagalog TikTok script
  → Checks TikTok compliance (rewrites if needed)
  → Generates 4 realistic scenes (hands holding your product)
  → Animates scenes into motion video clips
  → Generates Filipina voiceover (Jessica voice)
  → Burns TikTok-style word-by-word captions
  → Outputs final MP4 ready to post
```

### 3.4 Three Content Modes

| Mode | What you provide | What AI does | Best for |
|------|-----------------|-------------|----------|
| **Product photo** | 1 product image | Generates realistic in-use scenes, video, voiceover, captions | Daily content (recommended) |
| **Your video clips** | 2-3 phone recordings | Adds voiceover + captions to your real footage | Highest conversion |
| **Full AI** | Just the product name | Generates everything from scratch | Testing new products cheap |

### 3.5 Review Before Posting

Check these in the results:

| Check | What to look for |
|-------|-----------------|
| **Compliance badge** | Should say "TikTok Compliant" (green) |
| **Script** | Reads naturally in Tagalog, no weird phrasing |
| **Video** | Product looks correct, no duplicates/distortion |
| **Caption** | Has #ad and #AIgenerated hashtags |
| **Voiceover** | Sounds natural, matches the video length |

If compliance failed, try:
- Simpler product name (less adjectives)
- Remove claims from the name (no "best", "miracle", "clinically proven")

---

## Part 4: Posting to TikTok

### 4.1 Transfer Video to Phone

**Option A — Direct download:**
- Click "Download MP4" in the results
- Transfer via USB cable, Google Drive, or Telegram self-chat

**Option B — Cloud:**
- Upload MP4 to Google Drive
- Open Drive on phone → download to camera roll

### 4.2 Post the Video

1. Open TikTok → tap **+** → **Upload** → select your MP4
2. Trim if needed (keep it tight)
3. **Add caption:** Copy-paste the TikTok Caption from the app
4. **Add product link:** If TikTok Shop approved, tap "Add product" and link the item
5. **AIGC label (REQUIRED):** Tap More options (...) → Turn ON **"AI-generated content"**
6. **Add trending sound (optional):** Pick a trending sound, volume at 10-15%
7. **Post**

### 4.3 After Posting

- **Reply to every comment** within the first hour (biggest algorithm boost)
- **Pin the best comment** that asks about the product
- **Don't delete** the video even if it underperforms
- Check analytics after 24 hours

---

## Part 5: Strategy for Sales

### 5.1 Posting Schedule (Philippine Time)

| Time | Why | Priority |
|------|-----|----------|
| 7-8 AM | Morning scroll | Medium |
| 12-1 PM | Lunch break | Medium |
| **6-9 PM** | Peak hours | **High — post your best content here** |
| 10-11 PM | Late night scroll | Medium |

**Space posts 2-3 hours apart.** Don't dump 5 videos at once.

### 5.2 Weekly Content Plan

| Day | Content | Notes |
|-----|---------|-------|
| Mon | Kontext video (new product) | Test new products |
| Tue | Kontext video (same product, different hook) | If Monday's got views |
| Wed | Your own video clip + AI voiceover | Highest trust content |
| Thu | Kontext video (new product) | Test another product |
| Fri | Kontext video (best performer recut) | Double down on winner |
| Sat | Your own video clip | Weekend = shopping time |
| Sun | Full AI video (test product) | Low effort, test ideas |

### 5.3 Content Mix

| Type | Per week | Purpose |
|------|----------|---------|
| Kontext (product photo) | 5-7 videos | Main content, easy to produce |
| Your own video clips | 2-3 videos | Highest trust, best conversion |
| Full AI (no photo) | 1-2 videos | Test new products cheap |

### 5.4 Finding What Works

**Track these numbers in TikTok Analytics:**

| Metric | What it means | Good number |
|--------|--------------|-------------|
| Views | How many saw it | 500+ per video |
| Watch time | How long they watched | 80%+ completion |
| Shares | People sending to friends | Any shares = good |
| Comments | Engagement | 5+ comments |
| Profile visits | Interest in your other content | 10+ per video |
| Link clicks | People clicking your affiliate | This = money |

### 5.5 When a Video Hits

If a video gets 10,000+ views:
1. Make 3 more videos for the same product (different hooks)
2. Film your own video clip of that product (highest conversion)
3. Post a follow-up: "ang daming nagtatanong about this..."
4. Pin the affiliate link comment

### 5.6 The 30-Day Playbook

| Week | Focus | Expected result |
|------|-------|----------------|
| 1 | Post daily, test 5-7 different products | Learning what gets views |
| 2 | Double down on products that got views | First viral potential |
| 3 | Add your own video clips for top performers | First sales |
| 4 | Scale winning products, 2-3 posts/day | Consistent sales |

---

## Part 6: Revenue Expectations

| Timeline | Realistic expectation |
|----------|----------------------|
| Week 1-2 | 0-few sales, building audience |
| Week 3-4 | First consistent sales if posting daily |
| Month 2 | 2,000-10,000 PHP/month if 1-2 products hit |
| Month 3+ | Scale winners, 25,000+ PHP/month possible |

**Cost per video:** ~$1-2 (Kontext + video gen + voiceover)
**Revenue per sale:** 5-20% commission depending on product
**Break-even:** ~5-10 sales per month covers your API costs

---

## Part 7: What NOT to Do

- Don't delete underperforming posts (algorithm penalizes deletion)
- Don't post the same video twice (TikTok detects duplicates)
- Don't forget the AIGC toggle (can result in ban)
- Don't forget #ad (legal requirement for affiliate)
- Don't make claims the product can't back up
- Don't spam 10 videos at once (space 2-3 hours apart)
- Don't buy followers or engagement (gets you shadow banned)
- Don't use copyrighted music at high volume (use trending sounds at low volume)
- Don't give up before 30 days (most creators quit too early)

---

## Quick Reference: Post Checklist

Before every post, confirm:

- [ ] Video looks good (no distorted product)
- [ ] Caption copied from the app
- [ ] #ad is in the caption
- [ ] #AIgenerated is in the caption
- [ ] AIGC toggle is ON in post settings
- [ ] Product link added (if TikTok Shop approved)
- [ ] Posting during peak hours (6-9 PM PHT)
