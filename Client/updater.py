import socket
import requests
import json
import os
import sys
import subprocess
import threading
import ctypes
from packaging import version
import tkinter as tk
from tkinter import messagebox


UPDATE_URL = "https://raw.githubusercontent.com/ahad324/TransferX/main/Client/appcast.xml"
AppVersion = "0.0.8"
APP_NAME = "TransferX"
update_status_label = None

def is_connected():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False
    
# Determine the path to WinSparkle.dll
def get_winsparkle_path():
    if getattr(sys, 'frozen', False):
        # Running as a standalone application
        return os.path.join(os.path.dirname(sys.executable), "WinSparkle.dll")
    else:
        # Running in a Python environment
        return os.path.join(os.path.dirname(__file__), "WinSparkle.dll")

# Load WinSparkle DLL
winsparkle_path = get_winsparkle_path()
try:
    winsparkle = ctypes.CDLL(winsparkle_path)
except OSError as e:
    print(f"Error loading WinSparkle.dll from {winsparkle_path}: {e}")
    sys.exit(1)

# Initialize WinSparkle
def init_winsparkle():
    winsparkle.win_sparkle_set_appcast_url(UPDATE_URL.encode('utf-8'))
    winsparkle.win_sparkle_set_app_details(APP_NAME.encode('utf-8'), APP_NAME.encode('utf-8'), AppVersion.encode('utf-8'))
    winsparkle.win_sparkle_set_automatic_check_for_updates(1)  # Enable automatic update checks
    winsparkle.win_sparkle_set_update_check_interval(3600)  # Check for updates every hour (3600 seconds)
    winsparkle.win_sparkle_init()
    
def check_for_updates():
    try:
        winsparkle.win_sparkle_check_update_with_ui()
    except Exception as e:
        print(f"Error checking for updates: {e}")
        return None

def set_update_status(message):
    global update_status_label
    if update_status_label and update_status_label.winfo_exists():
        update_status_label.config(text=f"{message}\nVersion: {AppVersion}")
        
def show_update_notification(version):
    root = tk.Tk()
    root.withdraw()
    message = f"Hey there! We've got a shiny new version ({version}) of {APP_NAME} ready for you.\n\n" \
              f"Don't worry, I'll take care of the update for you. You can keep working while I do my thing!"
    messagebox.showinfo("Update Available", message)

def check_updates_async():
    if is_connected():
        init_winsparkle()
        threading.Thread(target=check_for_updates, daemon=True).start()
    else:
        set_update_status("No internet connection. Skipping update check.")

if __name__ == "__main__":
    check_updates_async()