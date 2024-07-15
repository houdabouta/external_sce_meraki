import os
import sys
import logging
import time
import requests

# Add the modules path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules import common, meraki_api
from modules.fetch_extra_data import MerakiFetcher  # Ensure the class is imported directly

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting main function")
    common.create_directories()
    last_fetch_time = common.load_last_fetch_time()

    try:
        # Fetch organization details
        logging.info("Fetching organization details")
        organization_details = meraki_api.get_organization_details()
        common.save_to_json(organization_details, 'organization_details.json')
        logging.info("Organization details fetched and saved successfully")

        # Fetch updates
        logging.info("Fetching updates")
        fetcher = MerakiFetcher()
        first_run_success = fetcher.fetch_extra_data()
        if not first_run_success:
            logging.info("Retrying fetch updates due to an error in the first run")
            time.sleep(5)  # Wait for a short period before retrying
            fetcher.fetch_extra_data()
        logging.info("Updates fetched successfully")
        # Update the last fetch time
        common.save_last_fetch_time()
        logging.info("Last fetch time updated successfully")

    except requests.HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
        if e.response.status_code == 429:
            retry_after = int(e.response.headers.get('Retry-After', 1))
            logging.warning(f"Rate limit hit. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            main()
        elif e.response.status_code in [500, 502, 503, 504]:
            logging.warning("Server error. Retrying...")
            time.sleep(5)
            main()
        else:
            logging.error(f"API error details: {e.response.text}")
    except requests.RequestException as e:
        logging.error(f"Request exception occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    logging.info("Starting Meraki Dashboard data fetching script")
    main()
    logging.info("Script finished executing")
