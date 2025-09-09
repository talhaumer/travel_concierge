import os
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

# API Keys
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
RAPI_API_HOST = os.getenv("RAPI_API_HOST", "sky-scrapper.p.rapidapi.com")
RAPID_API_KEY = os.getenv("RAPID_API_KEY")
# Default settings
DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE", "en-US")

# External hosts
SKY_SCRAPPER_HOST = "sky-scrapper.p.rapidapi.com"
GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"

# Other constants (like retries, timeouts, etc.)
MAX_RETRIES = 2
TIMEOUT_SECS = 10
