import requests
import logging
import time
from .common import fetch_data, check_api_limits, save_to_json
from .config import MERAKI_BASE_URL, MERAKI_ORG_ID, MERAKI_API_KEY, USER_AGENT

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class MerakiAPIError(Exception):
    """Custom exception for Meraki API errors."""
    pass

def get_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
        "User-Agent": USER_AGENT
    }

def fetch_data_with_error_handling(url, params=None):
    """Fetch data from the Meraki API with error handling and retry logic."""
    headers = get_headers()
    while url:
        try:
            response = requests.get(url, headers=headers, params=params)
            check_api_limits(response)

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                logging.warning(f"Rate limit reached. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response.json()

        except requests.HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            if e.response.status_code == 429:
                retry_after = int(e.response.headers.get('Retry-After', 1))
                logging.warning(f"Rate limit hit. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
            elif e.response.status_code in [500, 502, 503, 504]:
                logging.warning("Server error. Retrying...")
                time.sleep(5)
            else:
                logging.error(f"API error details: {e.response.text}")
                raise MerakiAPIError(f"API error: {e.response.text}") from e
        except requests.RequestException as e:
            logging.error(f"Request exception occurred: {e}")
            raise MerakiAPIError(f"Request error: {e}") from e
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            raise MerakiAPIError(f"Unexpected error: {e}") from e

def get_networks():
    """Get networks for the organization from the Meraki API."""
    url = f"{MERAKI_BASE_URL}/organizations/{MERAKI_ORG_ID}/networks"
    logging.info(f"Fetching networks from {url}")
    return fetch_data_with_error_handling(url)

def get_devices():
    """Get devices for the organization from the Meraki API."""
    url = f"{MERAKI_BASE_URL}/organizations/{MERAKI_ORG_ID}/devices"
    logging.info(f"Fetching devices from {url}")
    return fetch_data_with_error_handling(url)

def get_ssids(network_id):
    """Get SSIDs for a given network."""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/wireless/ssids"
    logging.info(f"Fetching SSIDs for network {network_id}")
    ssids = fetch_data_with_error_handling(url)
    if not ssids:
        logging.warning(f"No SSIDs found for network {network_id}")
    logging.debug(f"SSIDs fetched for network {network_id}: {ssids}")
    return ssids

def get_access_points(network_id):
    """Get access points for a given network."""
    url = f"{MERAKI_BASE_URL}/networks/{network_id}/devices"
    logging.info(f"Fetching access points for network {network_id}")
    devices = fetch_data_with_error_handling(url)
    access_points = [device for device in devices if device['model'].startswith('MR')]
    logging.debug(f"Access points for network {network_id}: {access_points}")
    return access_points

def get_organization_details():
    """Fetch all details about the organization, including networks, devices, and access points."""
    organization_details = {'networks': []}
    
    networks = get_networks()
    devices = get_devices()
    
    for network in networks:
        network_id = network['id']
        product_types = network.get('productTypes', [])
        logging.info(f"Processing network {network_id} with product types: {product_types}")

        ssids = []
        if 'wireless' in product_types:
            ssids = get_ssids(network_id)
            # logging.info(f"SSIDs for network {network_id}: {ssids}")

        network_details = {
            'network': network,
            'devices': [device for device in devices if device['networkId'] == network_id],
            'access_points': get_access_points(network_id),
            'ssids': ssids
        }
        organization_details['networks'].append(network_details)
    
    return organization_details

if __name__ == "__main__":
    logging.info("Starting Meraki Dashboard data fetching script")
    organization_details = get_organization_details()
    save_to_json(organization_details, 'results/meraki_data/organization_details.json')
    logging.info("Data fetched and saved successfully")
