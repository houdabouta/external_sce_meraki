import os
import sys
import logging
import time
import requests
import asyncio
import json

# Add the modules path to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules import common, meraki_api, cloudifi_api
from modules.fetch_extra_data import MerakiFetcher
from modules.cloudifi_api import CloudiFi

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    logging.info("Starting main function")
    common.create_directories()
    last_fetch_time = common.load_last_fetch_time()

    try:
        # # Fetch organization details
        # logging.info("Fetching organization details")
        # organization_details = meraki_api.get_organization_details()
        # common.save_to_json(organization_details, 'organization_details.json')
        # logging.info("Organization details fetched and saved successfully")

        # # Fetch updates
        # logging.info("Fetching additionnal details")
        # fetcher = MerakiFetcher()
        # first_run_success = fetcher.fetch_extra_data()
        # if not first_run_success:
        #     logging.info("Retrying fetch updates due to an error in the first run")
        #     time.sleep(5)  # Wait for a short period before retrying
        #     fetcher.fetch_extra_data()
        # logging.info("Updates fetched successfully")
        # # Update the last fetch time
        # common.save_last_fetch_time()
        # logging.info("Last fetch time updated successfully")

        # Propagate Meraki data to Cloudi-FI
        logging.info("Initializing CloudiFi class")
        cf = CloudiFi()

        logging.info("Fetching and saving details from CloudiFi")
        loop = asyncio.get_event_loop()
        loop.run_until_complete(cf.fetch_and_save_details())
        logging.info("Details fetched and saved successfully")

        logging.info("Loading Meraki data from JSON file")
        with open("results/meraki_data/networks_devices_ssids.json") as f:
            meraki_data = json.load(f)
        logging.info("Meraki data loaded successfully")

        logging.info("Preparing location details")
        cf.prepare_location_details(meraki_data)
        logging.info("Location details prepared successfully")

        logging.info("Creating locations in CloudiFi from the saved JSON file")
        loop.run_until_complete(cf.create_locations_from_saved_data())
        logging.info("All locations created successfully")
        
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
