"""Populate Google Sheet with 30-Day TikTok Posting Plan."""
import gspread

SHEET_ID = "1tlMlck70AXHkOOXupk0KgHQarwXg6i9uusWIBhPwNjg"
CREDS_FILE = "google-creds.json"

# 30-day plan data: (date, day, time, shopee_search, pipeline_input, status, notes)
PLAN = [
    # WEEK 1
    ("2026-04-16", "Day 1", "12:00 PM", "die cast SUV toy", "Blue Die-Cast Luxury SUV Toy", "Posted", ""),
    ("2026-04-16", "Day 1", "6:00 PM", "land rover die cast", "Orange Land Rover Die-Cast Model", "Scheduled", ""),
    ("2026-04-16", "Day 1", "9:00 PM", "robot action figure movable", "Blue Robot Action Figure Movable Joints", "Scheduled", ""),
    ("2026-04-17", "Day 2", "12:00 PM", "die cast SUV toy black", "Black Die-Cast Luxury SUV Toy", "Scheduled", ""),
    ("2026-04-17", "Day 2", "6:00 PM", "hello kitty plush toy", "Hello Kitty Sanrio Soft Plush Toy Pink", "", ""),
    ("2026-04-17", "Day 2", "9:00 PM", "spider man action figure", "Spider-Man Marvel Action Figure Poseable", "", ""),
    ("2026-04-18", "Day 3", "12:00 PM", "mini building blocks city", "Mini Building Blocks City Set 200pcs", "", ""),
    ("2026-04-18", "Day 3", "6:00 PM", "monster truck toy big wheels", "Big Wheel Monster Truck Toy with Suspension", "", ""),
    ("2026-04-18", "Day 3", "9:00 PM", "naruto action figure", "Naruto Uzumaki Action Figure Movable Joints", "", ""),
    ("2026-04-19", "Day 4", "12:00 PM", "squishy toy cute animal", "Cute Animal Squishy Stress Relief Toy Soft", "", ""),
    ("2026-04-19", "Day 4", "6:00 PM", "dinosaur toy sound lights", "Dinosaur T-Rex Toy with Sound and Lights", "", ""),
    ("2026-04-19", "Day 4", "9:00 PM", "transformers figure bumblebee", "Transformers Bumblebee Action Figure Poseable", "", ""),
    ("2026-04-20", "Day 5", "12:00 PM", "keychain plush cute", "Cute Backpack Keychain Plush Toy Mini", "", ""),
    ("2026-04-20", "Day 5", "6:00 PM", "RC car off road remote control", "Remote Control Off-Road Truck with LED Lights", "", ""),
    ("2026-04-20", "Day 5", "9:00 PM", "gundam model kit", "Gundam RX-78 Model Kit Movable Joints", "", ""),
    ("2026-04-21", "Day 6", "12:00 PM", "play doh clay set colors", "Play-Doh Style Clay Set 12 Colors", "", ""),
    ("2026-04-21", "Day 6", "6:00 PM", "excavator toy truck", "Excavator Construction Truck Toy Yellow", "", ""),
    ("2026-04-21", "Day 6", "9:00 PM", "dragon ball z figure goku", "Dragon Ball Z Goku Figure Super Saiyan", "", ""),
    ("2026-04-22", "Day 7", "12:00 PM", "bubble gun toy LED", "Bubble Gun Toy with LED Lights Automatic", "", "CHECK ANALYTICS"),
    ("2026-04-22", "Day 7", "6:00 PM", "police car toy siren lights", "Police Car Toy with Siren and Flashing Lights", "", ""),
    ("2026-04-22", "Day 7", "9:00 PM", "one piece luffy figure", "One Piece Luffy Action Figure Gear 5", "", "Identify Winner 1 & 2"),
    # WEEK 2
    ("2026-04-23", "Day 8", "12:00 PM", "[W1 search new product]", "[W1 descriptive name]", "", ""),
    ("2026-04-23", "Day 8", "6:00 PM", "[W2 search new product]", "[W2 descriptive name]", "", ""),
    ("2026-04-23", "Day 8", "9:00 PM", "fidget pop it toy", "Pop It Fidget Toy Rainbow Colors Stress Relief", "", ""),
    ("2026-04-24", "Day 9", "12:00 PM", "[W1 different product]", "[W1 descriptive name]", "", ""),
    ("2026-04-24", "Day 9", "6:00 PM", "cute cat plush stuffed toy", "Cute Cat Plush Stuffed Toy Soft Huggable", "", ""),
    ("2026-04-24", "Day 9", "9:00 PM", "[W2 different product]", "[W2 descriptive name]", "", ""),
    ("2026-04-25", "Day 10", "12:00 PM", "kitchen play set toy kids", "Kids Kitchen Play Set with Cooking Accessories", "", ""),
    ("2026-04-25", "Day 10", "6:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-04-25", "Day 10", "9:00 PM", "beyblade spinning top", "Beyblade Burst Spinning Top with Launcher", "", ""),
    ("2026-04-26", "Day 11", "12:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-04-26", "Day 11", "6:00 PM", "mini drone toy camera", "Mini Drone Toy with Camera and LED Lights", "", ""),
    ("2026-04-26", "Day 11", "9:00 PM", "[W1 different product]", "[W1 descriptive name]", "", ""),
    ("2026-04-27", "Day 12", "12:00 PM", "baby rattle toy soft", "Soft Baby Rattle Toy with Teether Colorful", "", ""),
    ("2026-04-27", "Day 12", "6:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-04-27", "Day 12", "9:00 PM", "pokemon figure pikachu", "Pokemon Pikachu Action Figure with Stand", "", ""),
    ("2026-04-28", "Day 13", "12:00 PM", "nerf foam blaster gun", "Foam Blaster Dart Gun Toy with Target Set", "", ""),
    ("2026-04-28", "Day 13", "6:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-04-28", "Day 13", "9:00 PM", "demon slayer figure tanjiro", "Demon Slayer Tanjiro Action Figure Poseable", "", ""),
    ("2026-04-29", "Day 14", "12:00 PM", "[W1 new product]", "[W1 descriptive name]", "", "CHECK ANALYTICS"),
    ("2026-04-29", "Day 14", "6:00 PM", "toy tool set kids pretend", "Kids Toy Tool Set with Drill and Helmet", "", ""),
    ("2026-04-29", "Day 14", "9:00 PM", "[W2 different product]", "[W2 descriptive name]", "", "Target: 300-500 followers"),
    # WEEK 3
    ("2026-04-30", "Day 15", "12:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-04-30", "Day 15", "6:00 PM", "[W1 different variant]", "[W1 descriptive name]", "", ""),
    ("2026-04-30", "Day 15", "9:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-05-01", "Day 16", "12:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-05-01", "Day 16", "6:00 PM", "board game family card game", "Family Card Game Fun Party Game for Kids", "", ""),
    ("2026-05-01", "Day 16", "9:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-05-02", "Day 17", "12:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-05-02", "Day 17", "6:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-05-02", "Day 17", "9:00 PM", "kids ukulele toy guitar", "Kids Ukulele Mini Guitar Toy Musical Instrument", "", ""),
    ("2026-05-03", "Day 18", "12:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-05-03", "Day 18", "6:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-05-03", "Day 18", "9:00 PM", "[W1 different variant]", "[W1 descriptive name]", "", ""),
    ("2026-05-04", "Day 19", "12:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-05-04", "Day 19", "6:00 PM", "slime kit DIY toy", "DIY Slime Kit with Glitter and Charms", "", ""),
    ("2026-05-04", "Day 19", "9:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-05-05", "Day 20", "12:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-05-05", "Day 20", "6:00 PM", "[W1 new product]", "[W1 descriptive name]", "", ""),
    ("2026-05-05", "Day 20", "9:00 PM", "[W2 different variant]", "[W2 descriptive name]", "", ""),
    ("2026-05-06", "Day 21", "12:00 PM", "[W1 new product]", "[W1 descriptive name]", "", "CHECK ANALYTICS"),
    ("2026-05-06", "Day 21", "6:00 PM", "[W2 new product]", "[W2 descriptive name]", "", ""),
    ("2026-05-06", "Day 21", "9:00 PM", "walkie talkie toy kids", "Kids Walkie Talkie Toy Long Range with Light", "", "Target: 700-1000 followers"),
    # WEEK 4
    ("2026-05-07", "Day 22", "12:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-07", "Day 22", "6:00 PM", "[Top winner different hook]", "[descriptive name]", "", ""),
    ("2026-05-07", "Day 22", "9:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-08", "Day 23", "12:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-08", "Day 23", "6:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-08", "Day 23", "9:00 PM", "magnetic tiles toy kids", "Magnetic Building Tiles Set for Kids Colorful", "", ""),
    ("2026-05-09", "Day 24", "12:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-09", "Day 24", "6:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-09", "Day 24", "9:00 PM", "[Top winner different hook]", "[descriptive name]", "", ""),
    ("2026-05-10", "Day 25", "12:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-10", "Day 25", "6:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-10", "Day 25", "9:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-11", "Day 26", "12:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-11", "Day 26", "6:00 PM", "shopee trending toys", "[trending toy descriptive name]", "", "Check Shopee trending"),
    ("2026-05-11", "Day 26", "9:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-12", "Day 27", "12:00 PM", "[Top winner different hook]", "[descriptive name]", "", ""),
    ("2026-05-12", "Day 27", "6:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-12", "Day 27", "9:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-13", "Day 28", "12:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-13", "Day 28", "6:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-13", "Day 28", "9:00 PM", "[Top winner different hook]", "[descriptive name]", "", ""),
    ("2026-05-14", "Day 29", "12:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-14", "Day 29", "6:00 PM", "[2nd winner new product]", "[descriptive name]", "", ""),
    ("2026-05-14", "Day 29", "9:00 PM", "[2nd winner different hook]", "[descriptive name]", "", ""),
    ("2026-05-15", "Day 30", "12:00 PM", "[Top winner best product]", "[descriptive name]", "", "MILESTONE"),
    ("2026-05-15", "Day 30", "6:00 PM", "[Top winner new product]", "[descriptive name]", "", ""),
    ("2026-05-15", "Day 30", "9:00 PM", "[2nd winner best product]", "[descriptive name]", "", "Apply TikTok Shop Affiliate"),
]

HEADER = ["Date", "Day", "Time", "Shopee Search", "Pipeline Input", "Status", "Views", "TikTok Caption", "First Comment", "TikTok Name (30 char)", "Notes"]

# Week colors (RGB)
WEEK_COLORS = {
    1: {"red": 1, "green": 1, "blue": 1},           # white
    2: {"red": 0.85, "green": 0.92, "blue": 1},      # light blue
    3: {"red": 0.85, "green": 1, "blue": 0.88},      # light green
    4: {"red": 1, "green": 0.96, "blue": 0.8},       # light yellow
}


def get_week(day_num):
    if day_num <= 7:
        return 1
    if day_num <= 14:
        return 2
    if day_num <= 21:
        return 3
    return 4


def main():
    print("Connecting to Google Sheets...")
    gc = gspread.service_account(filename=CREDS_FILE)
    sh = gc.open_by_key(SHEET_ID)
    ws = sh.sheet1

    print("Clearing existing data...")
    ws.clear()

    # Write header
    print("Writing header...")
    ws.append_row(HEADER)

    # Write all rows
    print(f"Writing {len(PLAN)} rows...")
    def trim_name(name, max_len=30):
        name = name.strip()
        if len(name) <= max_len:
            return name
        trimmed = name[:max_len].rsplit(' ', 1)[0]
        return trimmed if trimmed else name[:max_len]

    rows = []
    for row in PLAN:
        # Date, Day, Time, Shopee Search, Pipeline Input, Status, Views, Caption, First Comment, TikTok Name, Notes
        pipeline_input = row[4]
        tiktok_name = trim_name(pipeline_input) if not pipeline_input.startswith('[') else ""
        rows.append(list(row[:6]) + ["", "", "", tiktok_name, row[6]])
    ws.append_rows(rows)

    # Batch format everything in one call to avoid rate limits
    print("Formatting...")
    formats = []

    # Header
    formats.append({
        "range": "A1:K1",
        "format": {
            "textFormat": {"bold": True, "fontSize": 11},
            "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.2},
            "horizontalAlignment": "CENTER",
        }
    })

    # Color code weeks + milestone highlights
    milestone_days = {"Day 7", "Day 14", "Day 21", "Day 30"}
    for i, row in enumerate(PLAN):
        row_num = i + 2
        day_str = row[1]
        day_num = int(day_str.split(" ")[1])
        week = get_week(day_num)
        color = WEEK_COLORS[week]

        # Milestone rows get special color
        if day_str in milestone_days and row[2] == "9:00 PM":
            formats.append({
                "range": f"A{row_num}:K{row_num}",
                "format": {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 1, "green": 0.85, "blue": 0.85},
                }
            })
        else:
            formats.append({
                "range": f"A{row_num}:K{row_num}",
                "format": {"backgroundColor": color}
            })

    ws.batch_format(formats)
    ws.freeze(rows=1)
    ws.columns_auto_resize(0, 11)

    print(f"\nDone! Sheet populated with {len(PLAN)} entries.")
    print(f"Open: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")


if __name__ == "__main__":
    main()
