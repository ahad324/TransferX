import socket
import requests
import json
import os
import sys
import subprocess
import threading
from packaging import version
import tkinter as tk
from tkinter import messagebox

UPDATE_URL = "https://raw.githubusercontent.com/ahad324/TransferX/main/version.json"
CURRENT_VERSION = "0.0.7"
APP_NAME = "TransferX"
update_status_label = None

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def check_for_updates():
    try:
        response = requests.get(UPDATE_URL, timeout=10)
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
            # Use a batch file to handle the update process
            batch_content = f"""
@echo off
:retry
taskkill /F /IM {APP_NAME}.exe
if %errorlevel% neq 0 (
    timeout /t 2
    goto retry
)
move /Y "{update_file}" "{APP_NAME}.exe"
start "" "{APP_NAME}.exe"
del "%~f0"
            """
            with open("update.bat", "w") as batch_file:
                batch_file.write(batch_content)
            subprocess.Popen("update.bat", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit()
        except Exception as e:
            set_update_status(f"Error applying update: {e}")
            if os.path.exists(update_file):
                try:
                    os.remove(update_file)
                    set_update_status("Cleaned up update file after error.")
                except:
                    set_update_status("Failed to clean up update file.")
    else:
        set_update_status("Update downloaded. Please run the new executable to update.")

def show_update_notification(version):
    root = tk.Tk()
    root.withdraw()
    message = f"Hey there! We've got a shiny new version ({version}) of {APP_NAME} ready for you.\n\n" \
              f"Don't worry, I'll take care of the update for you. You can keep working while I do my thing!"
    messagebox.showinfo("Update Available", message)

def update_app():
    if not is_connected():
        set_update_status(f"No internet connection. Version {CURRENT_VERSION}")
        return
    
    update_info = check_for_updates()
    if update_info:
        set_update_status(f"New version {update_info['version']} available.")
        show_update_notification(update_info['version'])
        update_file = download_update(update_info['url'])
        if update_file:
            apply_update(update_file)
    else:
        set_update_status(f"Version {CURRENT_VERSION}")

def check_updates_async():
    threading.Thread(target=update_app, daemon=True).start()

if __name__ == "__main__":
    check_updates_async()