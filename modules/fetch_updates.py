import logging
import time
import requests
from .common import fetch_data, save_to_json, load_last_fetch_time, save_last_fetch_time, create_directories, check_api_limits
from .config import MERAKI_BASE_URL, MERAKI_ORG_ID, MERAKI_API_KEY, USER_AGENT

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MerakiFetcher:
    def __init__(self):
        self.base_url = MERAKI_BASE_URL
        self.org_id = MERAKI_ORG_ID
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Cisco-Meraki-API-Key": MERAKI_API_KEY,
            "User-Agent": USER_AGENT
        }

    def fetch_data_with_pagination(self, url, params=None):
        """Fetch data from the Meraki API with pagination support."""
        items = []
        while url:
            response = requests.get(url, headers=self.headers, params=params)
            check_api_limits(response)

            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                logging.warning(f"Rate limit reached. Retrying after {retry_after} seconds.")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            data = response.json()
            items.extend(data)

            # Check if there is a next page
            url = response.links.get('next', {}).get('url')
        return items

    def get_networks(self):
        """Get networks for the organization from the Meraki API."""
        url = f"{self.base_url}/organizations/{self.org_id}/networks"
        params = {'perPage': 100}
        logging.info(f"Fetching networks from {url}")
        return self.fetch_data_with_pagination(url, params)

    def get_devices(self, network_id):
        """Get devices for a given network."""
        url = f"{self.base_url}/networks/{network_id}/devices"
        params = {'perPage': 100}
        logging.info(f"Fetching devices for network {network_id}")
        return self.fetch_data_with_pagination(url, params)

    def get_ssids(self, network_id):
        """Get SSIDs for a given wireless network."""
        url = f"{self.base_url}/networks/{network_id}/wireless/ssids"
        logging.info(f"Fetching SSIDs for network {network_id}")
        try:
            ssids = self.fetch_data_with_pagination(url)
            logging.debug(f"Fetched SSIDs for network {network_id}: {ssids}")
            return ssids
        except Exception as e:
            logging.error(f"Failed to fetch SSIDs for network {network_id}: {e}")
            return []

    def fetch_network_details(self, network, last_fetch_time):
        """Fetch devices and SSIDs for a given network and return a combined structure."""
        network_id = network['id']
        network_type = network.get('productTypes', [])
        network_data = {
            'network': network,
            'devices': [],
            'ssids': []
        }
        try:
            # Fetch devices
            devices = self.get_devices(network_id)
            network_data['devices'] = devices

            # Fetch SSIDs if it's a wireless network
            if 'wireless' in network_type:
                ssids = self.get_ssids(network_id)
                if not ssids:
                    logging.warning(f"No SSIDs found for wireless network {network_id}")
                network_data['ssids'] = ssids
                logging.debug(f"Fetched SSIDs for network {network_id}: {ssids}")

        except Exception as e:
            logging.error(f"An error occurred while fetching details for network {network_id}: {e}")
        
        return network_data

    def fetch_all_network_details(self, networks, last_fetch_time):
        """Fetch devices and SSIDs for multiple networks without batching."""
        networks_data = {}
        for network in networks:
            network_data = self.fetch_network_details(network, last_fetch_time)
            networks_data[network['id']] = network_data
        return networks_data

    def fetch_updates(self):
        create_directories()  # Ensure directories are created
        last_fetch_time = load_last_fetch_time()
        try:
            # Fetch networks
            networks = self.get_networks()
            save_to_json(networks, 'networks.json')
            
            # Fetch devices and SSIDs for each network
            networks_data = self.fetch_all_network_details(networks, last_fetch_time)
            save_to_json(networks_data, 'networks_devices_ssids.json')
            
            # Save the aggregated data
            save_to_json(networks_data, 'networks_devices_ssids.json')
            
            # Update the last fetch time
            save_last_fetch_time()

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            return False  # Indicate failure
        return True  # Indicate success

if __name__ == "__main__":
    logging.info("Starting Meraki Dashboard data fetching script")
    fetcher = MerakiFetcher()
    fetcher.fetch_updates()
    logging.info("Script finished executing")
