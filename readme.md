# Hikvision User Data and Face Image Downloader

This Python script retrieves user information, face images, and card details from a Hikvision access control device using its ISAPI. It then saves this data to a JSON file and downloads the face images to a local directory.

## Prerequisites

- Python 3.6+
- `requests` library: Install using `pip install requests`

## Usage

1.  **Run the script:**
    ```bash
    python main.py
    ```
2.  **Enter the required information:**
    -   Base URL of the Hikvision device (e.g., `https://192.168.1.100`)
    -   Username for authentication
    -   Password for authentication
    -   Folder name where the output directory will be created. The output directory will have a time stamp added to the name.

3.  **Output:**
    -   The script will create a directory with the provided folder name and a timestamp.
    -   Inside this directory, you will find:
        -   `user_data.json`: A JSON file containing user information, including employee number, name, user type, face URL, local image path, and card details.
        -   Face images: Images of users' faces, named using their employee numbers (e.g., `12345.jpg`).

## Script Description

-   **`get_all_users(base_url, username, password)`:**
    -   Retrieves all users from the Hikvision device using the `/ISAPI/AccessControl/UserInfo/Search` endpoint.
    -   Handles pagination to retrieve all users, even if they exceed the maximum results per request.
-   **`get_user_face_url(base_url, username, password, employee_no)`:**
    -   Retrieves the face URL for a given employee number using the `/ISAPI/Intelligent/FDLib/FDSearch` endpoint.
-   **`download_image(url, filename, username, password)`:**
    -   Downloads an image from a given URL and saves it to a local file.
-   **`get_user_cards(base_url, username, password, employee_no)`:**
    -   Retrieves card information for a given employee number using the `/ISAPI/AccessControl/CardInfo/Search` endpoint.
-   **`main()`:**
    -   Prompts the user for input (base URL, username, password, folder name).
    -   Creates an output directory.
    -   Retrieves all users.
    -   For each user:
        -   Retrieves the face URL.
        -   Downloads the face image.
        -   Retrieves card information.
        -   Creates a filtered user data dictionary.
        -   Appends the user data to a list.
    -   Saves the user data to `user_data.json`.
    -   Prints a message indicating where the data and images were saved.
