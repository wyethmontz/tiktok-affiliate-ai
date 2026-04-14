import os
from supabase import create_client
from dotenv import load_dotenv

# Load the variables from your .env file
load_dotenv()

# -----------------------
# CONNECT TO SUPABASE
# -----------------------

# This pulls the keys you just saved in your .env file
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# -----------------------
# SAVE AD FUNCTION
# -----------------------
def save_ad(data):
    """
    This is your bridge between Python AI system and real database.
    It takes the AI results and pushes them into the 'ads' table.
    """
    
    response = supabase.table("ads").insert(data).execute()

    return response
