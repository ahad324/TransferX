import requests
import json
import os
import sys
import subprocess
import threading
import base64

GITHUB_API_URL = "https://api.github.com/repos/yourusername/yourrepo/contents/version.json"
CURRENT_VERSION = "0.0.5"
APP_NAME = "TransferX"

def check_for_updates():
    try:
        response = requests.get(GITHUB_API_URL)
        response.raise_for_status()
        content = response.json()['content']
        decoded_content = base64.b64decode(content).decode('utf-8')
        version_info = json.loads(decoded_content)
        
        app_type = "client"
        if version_info[app_type]['version'] > CURRENT_VERSION:
            return version_info[app_type]
        return None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None

def download_update(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        update_file = f"{APP_NAME}_update.exe"
        with open(update_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return update_file
    except Exception as e:
        print(f"Error downloading update: {e}")
        return None

def apply_update(update_file):
    if getattr(sys, 'frozen', False):
        subprocess.Popen([update_file, "/SILENT", "/CLOSEAPPLICATIONS"])
        sys.exit()
    else:
        print("Update downloaded. Please run the new executable to update.")

def update_app():
    update_info = check_for_updates()
    if update_info:
        print(f"New version {update_info['version']} available. Downloading...")
        update_file = download_update(update_info['url'])
        if update_file:
            print("Update downloaded. Applying update...")
            apply_update(update_file)
    else:
        print("No updates available.")

def check_updates_async():
    threading.Thread(target=update_app, daemon=True).start()