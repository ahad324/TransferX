import os
import re
import socket
import sys
from pathlib import Path

# Function to get the downloads folder
def get_downloads_folder():
    if sys.platform == "win32":
        return Path(os.environ['USERPROFILE']) / 'Downloads'
    elif sys.platform in ["darwin", "linux"]:
        return Path.home() / 'Downloads'
    else:
        return Path.home()

# Function to ensure the base directory exists
def ensure_base_dir_exists(base_dir):
    if not base_dir.exists():
        base_dir.mkdir(parents=True, exist_ok=True)

# Function to set the window icon
def set_window_icon(window):
    current_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    logo_path = os.path.join(current_dir, 'Logo', 'logo.ico')
    window.iconbitmap(logo_path)

# Function to center the window
def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    position_top = int(screen_height / 2 - height / 2)
    position_right = int(screen_width / 2 - width / 2)
    window.geometry(f'{width}x{height}+{position_right}+{position_top}')

# Function to sanitize the filename to avoid "Directory Traversal attack"
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# Function to format size
def format_size(bytes_size):
    """
    Format bytes into human readable string with appropriate unit.
    Automatically chooses between B, KB, MB, GB, TB based on size.
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    return f"{size:.2f} {units[unit_index]}"

# Validation Functions
def is_valid_ip(ip):
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
    return True

def is_valid_port(port):
    return 0 <= port <= 65535

def is_valid_chunk_size(size):
    return size > 0