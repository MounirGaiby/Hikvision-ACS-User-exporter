import requests
from requests.auth import HTTPDigestAuth
import json
import os
import urllib3
import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Disable InsecureRequestWarning

def get_all_users(base_url, username, password):
    """Retrieves all users from the device."""
    users = []
    search_position = 0
    max_results = 50

    while True:
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
            response = requests.post(url, headers=headers, data=json.dumps(payload), auth=HTTPDigestAuth(username, password), verify=False)
            response.raise_for_status()
            data = response.json()

            if "UserInfoSearch" in data and "UserInfo" in data["UserInfoSearch"]:
                user_info = data["UserInfoSearch"]["UserInfo"]
                users.extend(user_info)
                search_position += max_results

                if len(user_info) < max_results:
                    break
            else:
                break
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving users: {e}")
            break

    return users

def get_user_face_url(base_url, username, password, employee_no):
    """Retrieves the face URL for a given employee number."""
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
        response = requests.post(url, headers=headers, data=json.dumps(payload), auth=HTTPDigestAuth(username, password), verify=False)
        response.raise_for_status()
        data = response.json()
        if "MatchList" in data and len(data["MatchList"]) > 0:
            return data["MatchList"][0]["faceURL"]
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving face URL for {employee_no}: {e}")
        return None

def download_image(url, filename, username, password):
    """Downloads an image from a URL."""
    try:
        response = requests.get(url, stream=True, auth=HTTPDigestAuth(username, password), verify=False)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return False

def get_user_cards(base_url, username, password, employee_no):
    """Retrieves card information for a given employee number."""
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
        response = requests.post(url, headers=headers, data=json.dumps(payload), auth=HTTPDigestAuth(username, password), verify=False)
        response.raise_for_status()
        data = response.json()
        if "CardInfoSearch" in data and "CardInfo" in data["CardInfoSearch"]:
            return data["CardInfoSearch"]["CardInfo"]
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error retrieving card info for {employee_no}: {e}")
        return []

def main():
    base_url = input("Enter the base URL (e.g., https://192.168.171.110): ").rstrip('/')
    username = input("Enter the username: ")
    password = input("Enter the password: ")
    folder_name = input("Enter the folder name: ")

    now = datetime.datetime.now()
    time_stamp = now.strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(folder_name, time_stamp)

    os.makedirs(output_dir, exist_ok=True)

    users = get_all_users(base_url, username, password)
    user_data = []

    for user in users:
        employee_no = user["employeeNo"]
        face_url = get_user_face_url(base_url, username, password, employee_no)
        user["faceURL"] = face_url

        if face_url:
            filename = os.path.join(output_dir, f"{employee_no}.jpg")
            if download_image(face_url, filename, username, password):
                user["local_image_path"] = filename
            else:
                user["local_image_path"] = None
        else:
            user["local_image_path"] = None

        user_cards = get_user_cards(base_url, username, password, employee_no)
        user["cards"] = user_cards

        filtered_user = {
            "employeeNo": user["employeeNo"],
            "name": user["name"],
            "userType": user["userType"],
            "Valid": user["Valid"],
            "belongGroup": user["belongGroup"],
            "password": user["password"],
            "doorRight": user["doorRight"],
            "RightPlan": user["RightPlan"],
            "gender": user["gender"],
            "numOfCard": user["numOfCard"],
            "numOfFP": user.get("numOfFP", 0),
            "numOfFace": user["numOfFace"],
            "groupId": user["groupId"],
            "localAtndPlanTemplateId": user["localAtndPlanTemplateId"],
            "PersonInfoExtends": user["PersonInfoExtends"],
            "faceURL": user["faceURL"],
            "local_image_path": user["local_image_path"],
            "cards": user["cards"]
        }
        user_data.append(filtered_user)

    with open(os.path.join(output_dir, "user_data.json"), 'w') as f:
        json.dump(user_data, f, indent=4)

    print(f"User data and images saved to the '{output_dir}' directory.")

if __name__ == "__main__":
    main()