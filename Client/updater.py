import socket
import requests
import sys
import psutil
import subprocess
import threading
from packaging import version
from utility import get_downloads_folder
from pathlib import Path

GITHUB_API_URL = "https://api.github.com/repos/ahad324/TransferXClient/releases/latest"
AppVersion = "1.0.0"
APP_NAME = "TransferX"
version_label = None

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def set_version_label(label):
    global version_label
    version_label = label

def set_update_status(message):
    global version_label
    if version_label and version_label.winfo_exists():
        version_label.config(text=message)
        version_label.update_idletasks()

def check_for_updates():
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        release_info = response.json()
        latest_version = release_info['tag_name']
        
        # Check if the available version is newer
        if version.parse(latest_version) > version.parse(AppVersion):
            return release_info
        return None
    except Exception as e:
        set_update_status(f"Error checking for updates: {e}")
        return None

def download_update(asset):
    try:
        downloads_folder = get_downloads_folder()  # Get the Downloads folder path
        file_name = asset['name']  # Extract the file name from the asset
        update_file = downloads_folder / file_name  # Save with the same name and extension
        
        with requests.get(asset['browser_download_url'], stream=True, timeout=30) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        percentage = (downloaded / total_size) * 100
                        set_update_status(f"Downloading update... {percentage:.1f}%")
        
        set_update_status("Download complete. Preparing to install...")
        return update_file
    except requests.RequestException as e:
        set_update_status(f"Error downloading update: {e}")
        return None

def terminate_existing_app():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'] == f"{APP_NAME}.exe":
                proc.terminate()
                proc.wait()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def apply_update(update_file):
    if getattr(sys, 'frozen', False):
        try:
            # Run the installer silently with the correct extension
            subprocess.Popen([str(update_file), "/VERYSILENT"], shell=True)
            
            # Terminate the existing app
            terminate_existing_app()
            sys.exit()
        except Exception as e:
            set_update_status(f"Error applying update: {e}")
    else:
        set_update_status("Update downloaded. Please run the new executable to update.")

def update_app():
    if not is_connected():
        set_update_status(f"version {AppVersion}")
        return
    
    update_info = check_for_updates()
    if update_info:
        set_update_status(f"New version {update_info['tag_name']} found. Downloading update...")
        
        # Download the first available asset
        if update_info['assets']:
            asset = update_info['assets'][0]  # Take the first available asset
            update_file = download_update(asset)
            
            if update_file:
                apply_update(update_file)
        else:
            set_update_status("No update assets found.")
    else:
        set_update_status(f"version {AppVersion}")

def check_updates_async():
    threading.Thread(target=update_app, daemon=True).start()

if __name__ == "__main__":
    check_updates_async()
