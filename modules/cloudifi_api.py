import os
import requests
import json
# from .commmon import make_request
from modules.common import create_directories
from .config import CLOUDIFI_REFRESH_TOKEN, CLOUDIFI_BASE_URL, CLOUDIFI_TEMPLATE_ID

class CloudiFi:
    def __init__(self):
        self.cf_base_url = config.CLOUDIFI_BASE_URL
        self.cf_refresh_token = config.CLOUDIFI_REFRESH_TOKEN
        self.cf_template_id = config.CLOUDIFI_TEMPLATE_ID
        self.token = self.authenticate()

    def authenticate(self):
        url = f"{self.cf_base_url}/auth/form"
        headers = {'Content-Type': 'application/json'}
        data = {'refresh_token': self.cf_refresh_token}

        response = requests.post(url, headers=headers, json=data)
        if response.status_code not in [200, 201]:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")
        return response.json().get('token')

    def fetch_and_save_details(self):
        endpoints = ['countries', 'timezones', 'langs']
        headers = {'Authorization': f'Bearer {self.token}'}
        details = {}

        for endpoint in endpoints:
            url = f"{self.cf_base_url}/{endpoint}"
            response = requests.get(url, headers=headers)
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to fetch {endpoint}: {response.status_code} - {response.text}")
            details[endpoint] = response.json()

        create_directories("results/cloudi_fi")
        with open("results/cloudi_fi/details.json", "w") as f:
            json.dump(details, f, indent=4)

        return details

    def create_locations(self, meraki_data):
        with open("results/cloudi_fi/details.json") as f:
            details = json.load(f)
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        for network in meraki_data['networks']:
            location_data = {
                "name": network["name"],
                "lang": f"/langs/{details['langs'][0]['id']}",
                "template": f"/templates/{self.cf_template_id}",
                "timezone": f"/timezones/{details['timezones'][0]['id']}",
                "country": f"/countries/{details['countries'][0]['id']}",
                "addressLocality": network["address"],
                "postalCode": network["postal_code"],
                "streetAddress": network["address"],
                "bandwidthIn": 0,
                "bandwidthOut": 0,
                "identifiers": [
                    {
                        "key": device["mac"],
                        "alias": device["name"]
                    }
                    for device in network["devices"]
                ]
            }
            url = f"{self.cf_base_url}/locations"
            response = requests.post(url, headers=headers, json=location_data)
            if response.status_code not in [200, 201]:
                raise Exception(f"Failed to create location: {response.status_code} - {response.text}")

if __name__ == "__main__":
    cf = CloudiFi()
    cf.fetch_and_save_details()
    with open("results/meraki_data/networks_devices_ssids.json") as f:
        meraki_data = json.load(f)
    cf.create_locations(meraki_data)