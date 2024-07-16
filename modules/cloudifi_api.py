import os
import json
import requests
import logging
import asyncio
import aiohttp
from aiohttp import ClientSession, ClientResponseError
from .config import CLOUDIFI_BASE_URL, CLOUDIFI_REFRESH_TOKEN, CLOUDIFI_TEMPLATE_ID, CLOUDIFI_DATA_DIR
from modules import common 
from .common import create_directories

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CloudiFi:
    def __init__(self):
        self.cf_base_url = CLOUDIFI_BASE_URL
        self.cf_refresh_token = CLOUDIFI_REFRESH_TOKEN
        self.cf_template_id = CLOUDIFI_TEMPLATE_ID
        self.details_file = os.path.join(CLOUDIFI_DATA_DIR, "details.json")
        # self.cf_refresh_token = self.authenticate()

    # def authenticate(self):
    #     url = f"{self.cf_base_url}/auth/form"
    #     headers = {'Content-Type': 'application/json'}
    #     data = {'refresh_token': self.cf_refresh_token}

    #     try:
    #         response = requests.post(url, headers=headers, json=data)
    #         response.raise_for_status()
    #         token = response.json().get('token')
    #         logging.info("Authentication successful")
    #         return token
    #     except requests.exceptions.RequestException as e:
    #         logging.error(f"Authentication failed: {e}")
    #         if response is not None:
    #             logging.error(f"Request URL: {url}")
    #             logging.error(f"Request Headers: {headers}")
    #             logging.error(f"Request Body: {json.dumps(data)}")
    #             logging.error(f"Response Status Code: {response.status_code}")
    #             logging.error(f"Response Text: {response.text}")
    #         raise

    async def fetch_and_save_details(self):
        async with aiohttp.ClientSession() as session:
            # self.cf_refresh_token = await self.authenticate(session)
            details = await self.fetch_details(session)
            common.create_directories()
            with open(self.details_file, "w") as f:
                json.dump(details, f, indent=4)
            logging.info(f"Saved details to {self.details_file}")

    async def fetch_details(self, session):
        urls = {
            "langs": f"{self.cf_base_url}/langs",
            "countries": f"{self.cf_base_url}/countries",
            "timezones": f"{self.cf_base_url}/timezones"
        }

        headers = {
            'Authorization': f'Bearer {self.cf_refresh_token}'
        }

        details = {}
        for key, url in urls.items():
            async with session.get(url, headers=headers) as response:
                response.raise_for_status()
                details[key] = await response.json()
                logging.info(f"Fetched {key} successfully")

        return details

    def prepare_location_details(self, meraki_data):
        with open(self.details_file) as f:
            details = json.load(f)

        location_details = []
        for network_id, network_data in meraki_data.items():
            try:
                logging.info(f"Processing network {network_id}: {network_data}")
                network_name = network_data["network"]["name"]
                logging.info(f"Network name: {network_name}")

                device = network_data["devices"][0]
                logging.info(f"Device: {device}")

                address = device["address"]
                postcode = device["postcode"]
                country_name = device["country"]
                timezone_name = network_data["network"]["timeZone"]
                lang_name = "English"  # Assuming default language is English; adjust if needed

                logging.info(f"Country Name: {country_name}, Timezone Name: {timezone_name}, Language Name: {lang_name}")

                # Find IDs based on names
                country_id = self.get_id_by_name(details['countries']['hydra:member'], country_name, 'Country')
                timezone_id = self.get_id_by_name(details['timezones']['hydra:member'], timezone_name, 'Timezone')
                lang_id = self.get_id_by_name(details['langs']['hydra:member'], lang_name, 'Language')

                logging.info(f"Matched Country ID: {country_id}, Timezone ID: {timezone_id}, Language ID: {lang_id}")

                location_data = {
                    "name": network_name,
                    "lang": f"/langs/{lang_id}",
                    "template": f"/templates/{self.cf_template_id}",
                    "timezone": f"/timezones/{timezone_id}",
                    "country": f"/countries/{country_id}",
                    "addressLocality": address,
                    "postalCode": postcode,
                    "streetAddress": address,
                    "bandwidthIn": 0,
                    "bandwidthOut": 0,
                    "identifiers": [
                        {
                            "key": device["mac"],
                            "alias": device["name"]
                        }
                    ]
                }
                location_details.append(location_data)

            except KeyError as e:
                logging.error(f"Missing required field {e} in network {network_id}")
            except TypeError as e:
                logging.error(f"Unexpected error: {e} in network {network_id}")
            except Exception as e:
                logging.error(f"Unexpected error: {e} in network {network_id}")

        with open("results/cloudifi_data/location_details.json", "w") as f:
            json.dump(location_details, f, indent=4)
        logging.info("Saved location details to results/cloudifi_data/location_details.json")

    def get_id_by_name(self, items, name, item_type):
        logging.info(f"Searching for {item_type} with name {name}")
        for item in items:
            if item['name'].lower() == name.lower():
                logging.info(f"Found {item_type}: {item}")
                return item['id']
        logging.warning(f"{item_type} with name {name} not found.")
        return None

    async def create_locations_from_saved_data(self):
        with open("results/cloudifi_data/location_details.json") as f:
            location_details = json.load(f)

        async with aiohttp.ClientSession() as session:
            for location in location_details:
                await self.create_location(session, location)

    async def create_location(self, session, location_data):
        url = f"{self.cf_base_url}/locations"
        headers = {
            'Authorization': f'Bearer {self.cf_refresh_token}',
            'Content-Type': 'application/json'
        }

        async with session.post(url, headers=headers, json=location_data) as response:
            if response.status == 201:
                logging.info(f"Location {location_data['name']} created successfully.")
            else:
                try:
                    response_data = await response.json()
                    logging.error(f"Failed to create location {location_data['name']}. Response: {response_data}")
                except Exception as e:
                    logging