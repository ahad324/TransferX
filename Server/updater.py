import requests
import json
import os
import sys
import subprocess
import threading
import base64
from packaging import version
import socket
import tkinter as tk
from tkinter import messagebox

GITHUB_API_URL = "https://transferx.netlify.app/version.json"
CURRENT_VERSION = "0.0.5"
APP_NAME = "TransferXServer"

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def check_for_updates():
    if not is_connected():
        print("No internet connection. Skipping update check.")
        return None

    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        
        version_info = response.json()
        
        app_type = "server"
        if app_type in version_info and 'version' in version_info[app_type]:
            if version.parse(version_info[app_type]['version']) > version.parse(CURRENT_VERSION):
                return version_info[app_type]
        return None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None

def download_update(url):
    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            update_file = f"{APP_NAME}_update.exe"
            with open(update_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
        return update_file
    except requests.RequestException as e:
        print(f"Error downloading update: {e}")
        return None

def apply_update(update_file):
    if getattr(sys, 'frozen', False):
        try:
            subprocess.Popen([update_file, "/SILENT", "/CLOSEAPPLICATIONS"])
            sys.exit()
        except subprocess.SubprocessError as e:
            print(f"Error applying update: {e}")
    else:
        print("Update downloaded. Please run the new executable to update.")

def show_update_notification(version):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    message = f"A new version ({version}) of {APP_NAME} is available.\n\n" \
              f"The update will be downloaded and applied automatically.\n" \
              f"You can continue your work without interruption."
    messagebox.showinfo("Update Available", message)

def update_app():
    update_info = check_for_updates()
    if update_info:
        show_update_notification(update_info['version'])
        print(f"New version {update_info['version']} available. Downloading...")
        update_file = download_update(update_info['url'])
        if update_file:
            print("Update downloaded. Applying update...")
            apply_update(update_file)
    # If no update is available, the function silently exits

def check_updates_async():
    threading.Thread(target=update_app, daemon=True).start()

if __name__ == "__main__":
    check_updates_async()