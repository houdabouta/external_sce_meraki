import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Constants
API_KEY = os.getenv('MERAKI_API_KEY')
ORG_ID = os.getenv('MERAKI_ORG_ID')
USER_AGENT = os.getenv('USER_AGENT')
BASE_URL = "https://api.meraki.com/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-Cisco-Meraki-API-Key": API_KEY,
    "User-Agent": USER_AGENT
}
BATCH_LIMIT = int(os.getenv('BATCH_LIMIT', 100))  # Configurable batch limit, default to 100
RESULTS_DIR = 'results'
MERAKI_DATA_DIR = os.path.join(RESULTS_DIR, 'meraki_data')
LAST_FETCH_FILE = 'last_fetch.json'