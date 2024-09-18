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
from tkinter import messagebox, Label

GITHUB_API_URL = "https://transferx.netlify.app/version.json"
CURRENT_VERSION = "0.0.6"
APP_NAME = "TransferX"
# Global variables for update status
update_status_label = None
update_in_progress = False

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
        
        app_type = "client"
        if app_type in version_info and 'version' in version_info[app_type]:
            if version.parse(version_info[app_type]['version']) > version.parse(CURRENT_VERSION):
                return version_info[app_type]
        return None
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None
    
def set_update_status(message):
    global update_status_label
    if update_status_label and update_status_label.winfo_exists():
        update_status_label.config(text=message)
        
def download_update(url):
    try:
        with requests.get(url, stream=True, timeout=30) as response:
            response.raise_for_status()
            update_file = f"{APP_NAME}_update.exe"
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

def apply_update(update_file):
    if getattr(sys, 'frozen', False):
        try:
            set_update_status("Installing update...")
            subprocess.Popen([update_file, "/SILENT", "/CLOSEAPPLICATIONS"])
            set_update_status("Update installed. Restarting application...")
            sys.exit()
        except subprocess.SubprocessError as e:
            set_update_status(f"Error applying update: {e}")
    else:
        set_update_status("Update downloaded. Please run the new executable to update.")

def show_update_notification(version):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    message = f"A new version ({version}) of {APP_NAME} is available.\n\n" \
              f"The update will be downloaded and applied automatically.\n" \
              f"You can continue your work without interruption."
    messagebox.showinfo("Update Available", message)

def update_app():
    global update_in_progress
    if update_in_progress:
        return
    
    update_in_progress = True
    update_info = check_for_updates()
    if update_info:
        set_update_status(f"New version {update_info['version']} available.")
        update_file = download_update(update_info['url'])
        if update_file:
            apply_update(update_file)
    else:
        set_update_status("No updates available.")
    update_in_progress = False

def check_updates_async():
    threading.Thread(target=update_app, daemon=True).start()

if __name__ == "__main__":
    check_updates_async()