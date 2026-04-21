"""Sync the TikTok 30-Day Plan Google Sheet:
1. Auto-generate style-aware first comments (basket CTA for Affiliate, engagement-only for Discovery)
2. Auto-update TikTok Name (30 char) from Pipeline Input

Column layout (post Post_Style insert at G):
A Date | B Day | C Time | D Shopee Search | E Pipeline Input | F Status
G Post_Style | H Views | I TikTok Caption | J First Comment | K TikTok Name | L Notes
"""
import gspread
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

SHEET_ID = "1tlMlck70AXHkOOXupk0KgHQarwXg6i9uusWIBhPwNjg"
CREDS_FILE = "google-creds.json"

# 0-indexed array positions
PIPELINE_INPUT_IDX = 4    # E
POST_STYLE_IDX = 6        # G
CAPTION_IDX = 8           # I
FIRST_COMMENT_IDX = 9     # J
TIKTOK_NAME_IDX = 10      # K

# A1 write columns
FIRST_COMMENT_COL_A1 = "J"
TIKTOK_NAME_COL_A1 = "K"

EMOJI_TRAIL_RE = re.compile(
    r'[\U0001f447\U0001f446\U0001f6d2\U0001f923\U0001f602\U0001f60d\U0001f525\U0001f440]+\s*$'
)


def trim_name(name: str, max_len: int = 30) -> str:
    name = name.strip()
    if len(name) <= max_len:
        return name
    trimmed = name[:max_len].rsplit(' ', 1)[0]
    return trimmed if trimmed else name[:max_len]


def extract_question(lines: list[str]) -> str:
    """First non-hashtag line containing '?'."""
    for line in lines:
        if line.startswith("#"):
            continue
        if "?" in line:
            return line
    return ""


def build_affiliate_comment(lines: list[str]) -> str:
    """Engagement question + 'Tap the yellow basket 🛒'."""
    question = extract_question(lines)
    if question:
        clean_q = EMOJI_TRAIL_RE.sub('', question).strip()
        return f"{clean_q} Tap the yellow basket \U0001f6d2"
    return "Sulit na sulit ito! Tap the yellow basket \U0001f6d2"


gc = gspread.service_account(filename=CREDS_FILE)
sh = gc.open_by_key(SHEET_ID)
ws = sh.sheet1
records = ws.get_all_values()

comment_updates = []
name_updates = []
skipped_discovery = 0

for i, row in enumerate(records):
    if i == 0:
        continue  # header
    row_num = i + 1

    pipeline_input = row[PIPELINE_INPUT_IDX] if len(row) > PIPELINE_INPUT_IDX else ""
    caption = row[CAPTION_IDX] if len(row) > CAPTION_IDX else ""
    first_comment = row[FIRST_COMMENT_IDX] if len(row) > FIRST_COMMENT_IDX else ""
    current_tiktok_name = row[TIKTOK_NAME_IDX] if len(row) > TIKTOK_NAME_IDX else ""
    post_style = (row[POST_STYLE_IDX] if len(row) > POST_STYLE_IDX else "").strip().lower()

    # Discovery posts get neither first comment nor TikTok Name — the "photo-reel
    # aesthetic" strategy requires a clean pinned-slot and no product-title
    # overlay that reads as commerce. Only Affiliate rows need these fields.
    if post_style == "discovery":
        skipped_discovery += 1
        continue

    # 1. FIRST COMMENT — regenerate if caption exists AND comment is empty OR uses legacy basket language
    has_caption = bool(caption.strip())
    legacy_cta = any(s in first_comment.lower() for s in [
        "para sa link", "for link", "para ma-send"
    ])
    legacy_basket = "tap the basket" in first_comment.lower() and "yellow" not in first_comment.lower()
    needs_update = has_caption and (
        not first_comment.strip() or legacy_cta or legacy_basket
    )

    if needs_update:
        lines = [l.strip() for l in caption.split("\n") if l.strip()]
        comment_text = build_affiliate_comment(lines)
        comment_updates.append({
            'range': f'{FIRST_COMMENT_COL_A1}{row_num}',
            'values': [[comment_text]],
        })
        print(f"[Comment] Row {row_num} [A]: {comment_text[:80]}")

    # 2. TIKTOK NAME — update when pipeline_input is real + differs from current
    if pipeline_input.strip() and not pipeline_input.startswith('['):
        new_name = trim_name(pipeline_input)
        if new_name != current_tiktok_name:
            name_updates.append({
                'range': f'{TIKTOK_NAME_COL_A1}{row_num}',
                'values': [[new_name]],
            })
            print(f"[Name] Row {row_num}: '{pipeline_input[:40]}' -> '{new_name}'")

# Batch writes
all_updates = comment_updates + name_updates
if all_updates:
    for i in range(0, len(all_updates), 30):
        ws.batch_update(all_updates[i:i + 30])

print(f"\n{len(comment_updates)} first comments updated (Affiliate rows)")
print(f"{len(name_updates)} TikTok names updated (Affiliate rows)")
if skipped_discovery:
    print(f"{skipped_discovery} Discovery rows skipped — first comment + TikTok Name stay empty by design")
print(f"\nSheet: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
