import requests
from requests.auth import HTTPDigestAuth
import json
import os
import urllib3
import datetime
import logging

# Disable SSL warnings for simplicity (not recommended for production)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup basic logging configuration
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(asctime)s [%(levelname)s] %(message)s"
)

### Helper Functions

def get_all_users(base_url, username, password):
    """Retrieve all normal users from the device."""
    users = []
    search_position = 0
    max_results = 50
    logging.info("Starting to fetch users from device.")

    while True:
        logging.debug(f"Fetching users starting at position {search_position} with up to {max_results} results.")
        url = f"{base_url}/ISAPI/AccessControl/UserInfo/Search?format=json"
        payload = {
            "UserInfoSearchCond": {
                "searchID": "usersx",
                "searchResultPosition": search_position,
                "maxResults": max_results,
                "userType": "normal"
            }
        }
        headers = {'Content-Type': 'application/json'}

        try:
            response = requests.post(url, headers=headers, data=json.dumps(payload),
                                     auth=HTTPDigestAuth(username, password), verify=False)
            logging.debug(f"Received response with status code {response.status_code}.")
            response.raise_for_status()
            data = response.json()

            if "UserInfoSearch" in data and "UserInfo" in data["UserInfoSearch"]:
                user_info = data["UserInfoSearch"]["UserInfo"]
                logging.info(f"Retrieved {len(user_info)} users in current batch.")
                users.extend(user_info)
                search_position += max_results
                # If fewer users than max_results are returned, it is the last batch.
                if len(user_info) < max_results:
                    break
            else:
                logging.warning("Unexpected response structure; stopping user retrieval.")
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Error retrieving users: {e}")
            break

    logging.info(f"Total users fetched: {len(users)}.")
    return users

def get_user_face_url(base_url, username, password, employee_no):
    """Get the face image URL for a specific user."""
    logging.info(f"Retrieving face URL for employee number: {employee_no}.")
    url = f"{base_url}/ISAPI/Intelligent/FDLib/FDSearch?format=json"
    payload = {
        "searchResultPosition": 0,
        "maxResults": 1,
        "faceLibType": "blackFD",
        "FDID": "1",
        "FPID": employee_no
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload),
                                 auth=HTTPDigestAuth(username, password), verify=False)
        logging.debug(f"Face URL response code: {response.status_code}.")
        response.raise_for_status()
        data = response.json()
        if "MatchList" in data and len(data["MatchList"]) > 0:
            face_url = data["MatchList"][0]["faceURL"]
            logging.info(f"Face URL found for employee number {employee_no}.")
            return face_url
        else:
            logging.warning(f"No face URL found for employee number {employee_no}.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving face URL for {employee_no}: {e}")
        return None

def download_image(url, filename, username, password, max_retries=2):
    """Download an image from a URL with retries."""
    logging.info(f"Starting download for image from URL: {url}.")
    attempts = 0
    while attempts <= max_retries:
        try:
            logging.debug(f"Download attempt {attempts + 1} for {url}.")
            response = requests.get(url, stream=True, auth=HTTPDigestAuth(username, password), verify=False)
            logging.debug(f"Download response code: {response.status_code}.")
            response.raise_for_status()
            with open(filename, 'wb') as f:
                # Write image data in chunks to handle large files
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"Image successfully downloaded and saved to {filename}.")
            return True
        except requests.exceptions.RequestException as e:
            attempts += 1
            logging.error(f"Attempt {attempts} failed for downloading image from {url}: {e}")
            if attempts > max_retries:
                logging.error(f"Failed to download image from {url} after {max_retries + 1} attempts.")
                return False
            logging.info("Retrying image download...")
            
def get_user_cards(base_url, username, password, employee_no):
    """Retrieve card information for a specific user."""
    logging.info(f"Fetching card information for employee number: {employee_no}.")
    url = f"{base_url}/ISAPI/AccessControl/CardInfo/Search?format=json"
    payload = {
        "CardInfoSearchCond": {
            "searchID": "cards",
            "searchResultPosition": 0,
            "maxResults": 50,
            "EmployeeNoList": [{"employeeNo": employee_no}]
        }
    }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload),
                                 auth=HTTPDigestAuth(username, password), verify=False)
        logging.debug(f"Card info response code: {response.status_code}.")
        response.raise_for_status()
        data = response.json()
        if "CardInfoSearch" in data and "CardInfo" in data["CardInfoSearch"]:
            card_info = data["CardInfoSearch"]["CardInfo"]
            logging.info(f"Retrieved {len(card_info)} cards for employee number {employee_no}.")
            return card_info
        else:
            logging.warning(f"No card info found for employee number {employee_no}.")
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f"Error retrieving card info for {employee_no}: {e}")
        return []

### Main Function

def main():
    # Load last configuration if available
    logging.info("Attempting to load last configuration from file.")
    try:
        with open("last_config.json", "r") as f:
            last_config = json.load(f)
        logging.debug("Last configuration loaded successfully.")
    except FileNotFoundError:
        last_config = {}
        logging.info("No previous configuration file found; starting fresh.")

    if last_config:
        logging.info("Previous configuration detected:")
        print(f"  Base URL: {last_config.get('base_url')}")
        print(f"  Username: {last_config.get('username')}")
        print(f"  Folder Name: {last_config.get('folder_name')}")
        use_last = input("Use last configuration? (y/n): ").lower()
        if use_last == 'y':
            base_url = last_config.get('base_url', '')
            username = last_config.get('username', '')
            folder_name = last_config.get('folder_name', '')
            logging.info("Using last saved configuration.")
        else:
            base_url = input("Enter the base URL (e.g., https://192.168.171.110): ").rstrip('/')
            username = input("Enter the username: ")
            folder_name = input("Enter the folder name: ")
            logging.info("New configuration provided by user.")
    else:
        base_url = input("Enter the base URL (e.g., https://192.168.171.110): ").rstrip('/')
        username = input("Enter the username: ")
        folder_name = input("Enter the folder name: ")
        logging.info("User provided new configuration.")

    password = input("Enter the password: ")

    # Create output directory: data/<folder_name>/<timestamp>
    now = datetime.datetime.now()
    time_stamp = now.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("data", folder_name, time_stamp)
    try:
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Output directory created at {output_dir}.")
    except OSError as e:
        logging.error(f"Error creating output directory {output_dir}: {e}")
        return

    logging.info(f"Starting data retrieval from {base_url}.")
    users = get_all_users(base_url, username, password)
    if not users:
        logging.error("No users retrieved. Exiting the process.")
        return

    total_users = len(users)
    logging.info(f"Total users to process: {total_users}.")
    user_data = []
    successful_images = 0

    # Process each user and log the processing steps
    for i, user in enumerate(users, 1):
        employee_no = user.get("employeeNo", "unknown")
        logging.info(f"Processing user {i}/{total_users}: Employee No {employee_no}.")

        # Get and download face image
        face_url = get_user_face_url(base_url, username, password, employee_no)
        user["faceURL"] = face_url

        if face_url:
            filename = os.path.join(output_dir, f"{employee_no}.jpg")
            if download_image(face_url, filename, username, password):
                user["local_image_path"] = f"{employee_no}.jpg"
                successful_images += 1
                logging.info(f"Image for user {employee_no} downloaded successfully.")
            else:
                user["local_image_path"] = None
                logging.warning(f"Failed to download image for user {employee_no}.")
        else:
            user["local_image_path"] = None
            logging.warning(f"No face URL available for user {employee_no}; skipping image download.")

        # Get card information for the user
        user_cards = get_user_cards(base_url, username, password, employee_no)
        user["cards"] = user_cards

        # Filter user data for JSON output
        filtered_user = {
            "employeeNo": user.get("employeeNo", ""),
            "name": user.get("name", ""),
            "userType": user.get("userType", ""),
            "Valid": user.get("Valid", {}),
            "belongGroup": user.get("belongGroup", ""),
            "password": user.get("password", ""),
            "doorRight": user.get("doorRight", ""),
            "RightPlan": user.get("RightPlan", []),
            "gender": user.get("gender", ""),
            "numOfCard": user.get("numOfCard", 0),
            "numOfFP": user.get("numOfFP", 0),
            "numOfFace": user.get("numOfFace", 0),
            "groupId": user.get("groupId", ""),
            "localAtndPlanTemplateId": user.get("localAtndPlanTemplateId", ""),
            "PersonInfoExtends": user.get("PersonInfoExtends", []),
            "faceURL": user.get("faceURL", None),
            "local_image_path": user.get("local_image_path", None),
            "cards": user.get("cards", [])
        }
        user_data.append(filtered_user)
        logging.debug(f"User {employee_no} processed and added to output list.")

    # Save user data to JSON file in the output directory
    try:
        with open(os.path.join(output_dir, "user_data.json"), 'w') as f:
            json.dump(user_data, f, indent=4)
        logging.info("User data saved to JSON file successfully.")
    except Exception as e:
        logging.error(f"Error saving user data to JSON: {e}")
        return

    # Save configuration for next run
    config_to_save = {
        "base_url": base_url,
        "username": username,
        "folder_name": folder_name
    }
    try:
        with open("last_config.json", "w") as f:
            json.dump(config_to_save, f)
        logging.info("Configuration saved for future runs.")
    except Exception as e:
        logging.error(f"Error saving configuration: {e}")

    # Print and log summary of processing results
    logging.info("Processing complete.")
    print("\nProcessing complete!")
    print(f"Total users processed: {total_users}")
    print(f"Images successfully downloaded: {successful_images}")
    print(f"Images failed to download: {total_users - successful_images}")
    print(f"User data and images saved to '{output_dir}' directory.")

if __name__ == "__main__":
    main()
