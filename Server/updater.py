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

GITHUB_API_URL = "https://api.github.com/repos/ahad324/TransferX/releases/latest"
AppVersion = "0.0.7"
APP_NAME = "TransferXServer"
update_status_label = None

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def check_for_updates():
    try:
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        release_info = response.json()
        latest_version = release_info['tag_name']
        if version.parse(latest_version) > version.parse(AppVersion):
            return release_info
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
        set_update_status(f"No internet connection. Version {AppVersion}")
        return
    
    update_info = check_for_updates()
    if update_info:
        set_update_status(f"New version {update_info['tag_name']} available.")
        show_update_notification(update_info['tag_name'])
        update_file = download_update(update_info['assets'][1]['browser_download_url'])
        if update_file:
            apply_update(update_file)
    else:
        set_update_status(f"Version {AppVersion}")

def check_updates_async():
    threading.Thread(target=update_app, daemon=True).start()

if __name__ == "__main__":
    check_updates_async()