
# external_sce_meraki

## About
This repository contains a project related to Meraki API integration, aimed at providing external SCE (Software Configuration and Environment) functionalities.

## Table of Contents
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Detailed Descriptions](#detailed-descriptions)
  - [cloudifi_api.py](#cloudifi_apipy)
  - [meraki_api.py](#meraki_apipy)
  - [fetch_data.py](#fetch_datapy)
- [Contributing](#contributing)
- [License](#license)

## Installation
1. Clone the repository:
    ```
    git clone https://github.com/houdabouta/external_sce_meraki.git
    ```
2. Navigate to the project directory:
    ```
    cd external_sce_meraki
    ```
3. Install the required dependencies:
    ```
    pip install -r requirements.txt
    ```

## Usage
To run the main script, use:
```
python main.py
```
Ensure that you have configured the necessary environment variables or configuration files as required by the project.

## Configuration
Create a `.env` file in the root directory of the project and add the following content:
```
MERAKI_API_KEY=value
MERAKI_ORG_ID=value
USER_AGENT="Cloudifi/houdatest/1.0 (myemail@example.com)"
CLOUDIFI_REFRESH_TOKEN=value
CLOUDIFI_BASE_URL=https://manage-api-v1.cloudi-fi.net
CLOUDIFI_TEMPLATE_ID=value
X_SWITCH_USER=value
```
This file contains sensitive information such as API keys and tokens required for accessing Meraki and Cloudi-Fi services.

## Project Structure
- `main.py`: Main script to run the project.
- `modules/`: Directory containing various modules for different functionalities.
- `requirements.txt`: List of dependencies required to run the project.
- `.gitignore`: Git ignore file specifying files and directories to be ignored.

## Detailed Descriptions
### `cloudifi_api.py`
This script includes functions to interact with the Cloudi-Fi API. It handles:
- Authentication using the provided refresh token.
- Fetching configuration templates and other necessary data from Cloudi-Fi.

### `meraki_api.py` and `fetch_data.py`
These scripts include functions to interact with the Meraki API. It manages:
- Authentication using the provided API key.
- Fetching network and device details, and other relevant configurations from Meraki.