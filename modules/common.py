import os
import logging
import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
from .config import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Retry strategy for HTTP requests
retry_strategy = Retry(
    total=3,
    backoff_factor=5,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["HEAD", "GET", "OPTIONS", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)

# def create_directories():
#     """Create directories for storing JSON data files."""
#     try:
#         os.makedirs(MERAKI_DATA_DIR, exist_ok=True)
#         logging.info(f"Directories {RESULTS_DIR} and {MERAKI_DATA_DIR} have been created or already exist.")
#     except Exception as e:
#         logging.error(f"Failed to create directories: {e}")

def create_directories():
    """Create directories for storing JSON data files."""
    try:
        os.makedirs(MERAKI_DATA_DIR, exist_ok=True)
        os.makedirs(CLOUDIFI_DATA_DIR, exist_ok=True)
        logging.info(f"Directories {MERAKI_DATA_DIR} and {CLOUDIFI_DATA_DIR} have been created or already exist.")
    except Exception as e:
        logging.error(f"Failed to create directories: {e}")

def save_to_json(data, filename):
    """Save data to a JSON file."""
    filepath = os.path.join(MERAKI_DATA_DIR, filename)
    try:
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=4)
        logging.info(f"Data has been written to {filepath}")
    except IOError as e:
        logging.error(f"Failed to write data to {filepath}: {e}")

def load_last_fetch_time():
    """Load the last fetch time from a JSON file."""
    try:
        if not os.path.exists(LAST_FETCH_FILE):
            save_last_fetch_time(0)
        with open(LAST_FETCH_FILE, 'r') as f:
            last_fetch = json.load(f)['last_fetch']
        logging.info(f"Last fetch time loaded: {last_fetch}")
        return last_fetch
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        logging.warning(f"Failed to load last fetch time: {e}")
        return 0

def save_last_fetch_time(timestamp=None):
    """Save the current time as the last fetch time to a JSON file."""
    current_time = timestamp if timestamp is not None else time.time()
    try:
        with open(LAST_FETCH_FILE, 'w') as f:
            json.dump({'last_fetch': current_time}, f)
        logging.info("Last fetch time has been updated")
    except IOError as e:
        logging.error(f"Failed to save last fetch time: {e}")

def fetch_data(url, params=None):
    """Fetch data from a given URL with optional parameters."""
    try:
        response = http.get(url, headers=HEADERS, params=params)
        check_api_limits(response)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as http_err:
        logging.error(f"HTTP error occurred while fetching data from {url}: {http_err}")
        raise
    except Exception as err:
        logging.error(f"An error occurred while fetching data from {url}: {err}")
        raise

def check_api_limits(response):
    """Check response headers for API limits and handle wait times if necessary."""
    if 'X-Rate-Limit-Limit' in response.headers and 'X-Rate-Limit-Remaining' in response.headers:
        limit = int(response.headers['X-Rate-Limit-Limit'])
        remaining = int(response.headers['X-Rate-Limit-Remaining'])
        if remaining == 0:
            reset_time = int(response.headers.get('X-Rate-Limit-Reset', 1))
            sleep_time = reset_time - time.time()
            if sleep_time > 0:
                logging.warning(f"API limit reached. Waiting for {sleep_time} seconds before continuing.")
                time.sleep(sleep_time)