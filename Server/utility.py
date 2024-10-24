import os
import re
import socket
import sys
from pathlib import Path

# Function to get the downloads folder
def get_downloads_folder():
    if os.name == "nt":  # Windows
        return Path(os.environ['USERPROFILE']) / 'Downloads'
    elif os.name == "posix":  # macOS or Linux
        return Path.home() / 'Downloads'
    else:
        return Path.home()

# Function to ensure the base directory exists
def ensure_base_dir_exists(bucket_dir):
    if not os.path.exists(bucket_dir):
        os.makedirs(bucket_dir, exist_ok=True)
        return True
    return False

# Function to sanitize the filename to avoid "Directory Traversal attack"
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# Function for IP validation
def is_valid_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True

# Function for port validation
def is_valid_port(port):
    return 0 <= port <= 65535

# Function for chunk size validation
def is_valid_chunk_size(size):
    return size > 0

# Function to set the window icon
def set_window_icon(window):
    current_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    logo_path = os.path.join(current_dir, 'Logo', 'logo.ico')
    window.iconbitmap(logo_path)