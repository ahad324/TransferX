import socket
import os
import sys
from pathlib import Path
import json
from threading import Thread, Event
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, font
import logging
import sqlite3
import re

# Determine the user's Downloads folder path
def get_downloads_folder():
    if sys.platform == "win32":
        return Path(os.environ['USERPROFILE']) / 'Downloads'
    elif sys.platform == "darwin":
        return Path.home() / 'Downloads'
    elif sys.platform == "linux":
        return Path.home() / 'Downloads'
    else:
        return Path.home()

# Determine the base directory for file operations
if getattr(sys, 'frozen', False):
    CURRENT_DIR = Path(sys._MEIPASS)
    BASE_DIR = get_downloads_folder() / 'TransferX Server'
else:
    CURRENT_DIR = Path(__file__).parent
    BASE_DIR = CURRENT_DIR
    
def ensure_base_dir_exists():
    if not BASE_DIR.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)

# Create the base directory if it doesn't exist
ensure_base_dir_exists()

# Constants
SERVER_IP = '0.0.0.0'
SERVER_PORT = 5000
CHUNK_SIZE = 4096
DELIMITER = "---END-HEADER---"
DB_FILE = os.path.join(BASE_DIR, 'server_data.db')
LOG_FILE = os.path.join(BASE_DIR, 'server.log')
BUCKET_DIR = os.path.join(BASE_DIR, 'bucket_storage')
FONT = "Segoe UI"


# Define colors
DARK_BG_COLOR = '#2E2E2E'
LIGHT_BG_COLOR = '#F0F2F5'

# Server control flags
server_running = False
stop_event = Event()
connections = []  # Track active connections

# To set the icon on every window
def set_window_icon(window):
    current_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    logo_path = os.path.join(current_dir, 'Logo', 'logo.ico')
    window.iconbitmap(logo_path)
    
# Initialize the Tkinter root window
root = tk.Tk()
root.title("TransferX Server Panel")
root.geometry("800x630")
root.minsize(300, 300)
set_window_icon(root)
root.configure(bg=DARK_BG_COLOR)
# Apply the font globally
root.option_add("*Font", font.Font(family=FONT))

# Tkinter variables
connection_count_var = tk.IntVar(value=0)
file_count_var = tk.IntVar(value=0)
data_received_var = tk.IntVar(value=0)
chunk_size_var = tk.IntVar(value=CHUNK_SIZE)
server_ip_var = tk.StringVar(value=SERVER_IP)
server_port_var = tk.IntVar(value=SERVER_PORT)
directory_var = tk.StringVar(value=BUCKET_DIR+"/")

# Style for the notebook tabs
style = ttk.Style()
style.configure("TNotebook.Tab", padding=[20, 10])

# Create a notebook with tabs
notebook = ttk.Notebook(root)
notebook.pack(pady=20, expand=True, fill="both")

# Frames for notebook tabs
log_frame = tk.Frame(notebook,padx=20)
log_frame.pack(fill=tk.BOTH, expand=True)
notebook.add(log_frame, text="Logs")

status_frame = tk.Frame(notebook)
notebook.add(status_frame, text="Status")

settings_frame = tk.Frame(notebook)
notebook.add(settings_frame, text="Settings")

# Create and pack the log text area
log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,bg=LIGHT_BG_COLOR,height=20,font=("Courier",10))
log_text.pack(pady=20, fill=tk.BOTH, expand=True)
log_text.insert(tk.END, "CLICK ON THE START SERVER BUTTON...\n")

# Status frame content
status_frame.grid_columnconfigure(0, weight=1)
status_frame.grid_columnconfigure(1, weight=1)
tk.Label(status_frame, text="Active Connections:",font=(FONT,12,"bold")).grid(row=0, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=connection_count_var).grid(row=0, column=1, padx=20, pady=10)

tk.Label(status_frame, text="Files Processed:",font=(FONT,12,"bold")).grid(row=1, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=file_count_var).grid(row=1, column=1, padx=20, pady=10)

tk.Label(status_frame, text="Data Received (bytes):",font=(FONT,12,"bold")).grid(row=2, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=data_received_var).grid(row=2, column=1, padx=20, pady=10)

tk.Label(status_frame, text="Chunk Size (bytes):",font=(FONT,12,"bold")).grid(row=3, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=chunk_size_var).grid(row=3, column=1, padx=20, pady=10)

# Settings frame content
settings_frame.grid_columnconfigure(0, weight=1)
settings_frame.grid_columnconfigure(1, weight=2)

tk.Label(settings_frame, text="Server IP:", anchor="e", font=(FONT, 12, "bold")).grid(row=0, column=0, padx=20, pady=10, sticky="e")
server_ip_entry = tk.Entry(settings_frame, textvariable=server_ip_var, font=( 12), width=30)
server_ip_entry.grid(row=0, column=1, padx=20, pady=10)

tk.Label(settings_frame, text="Port:", anchor="e", font=(FONT, 12, "bold")).grid(row=1, column=0, padx=20, pady=10, sticky="e")
server_port_entry = tk.Entry(settings_frame, textvariable=server_port_var, font=( 12), width=30)
server_port_entry.grid(row=1, column=1, padx=20, pady=10)

tk.Label(settings_frame, text="Chunk Size:", anchor="e", font=(FONT, 12, "bold")).grid(row=2, column=0, padx=20, pady=10, sticky="e")
chunk_size_entry = tk.Entry(settings_frame, textvariable=chunk_size_var, font=( 12), width=30)
chunk_size_entry.grid(row=2, column=1, padx=20, pady=10)

tk.Label(settings_frame, text="Storage Directory:", anchor="e", font=(FONT, 12, "bold")).grid(row=3, column=0, padx=20, pady=10, sticky="e")
directory_entry = tk.Entry(settings_frame, textvariable=directory_var, font=( 12), width=30)
directory_entry.grid(row=3, column=1, padx=20, pady=10)

apply_button = tk.Button(settings_frame, text="Apply", command=lambda:apply_settings(), height=2, width=10,bg="#4CAF50", fg="white", relief="raised",font=(FONT,10,"bold"))
apply_button.grid(row=4, column=0, columnspan=2, padx=20, pady=20, sticky="n")

# Button frame for server control
button_frame = tk.Frame(root)
button_frame.config(bg=DARK_BG_COLOR)
button_frame.pack(pady=20)

start_button = tk.Button(button_frame, text="Start Server", command=lambda: start_server(), height=2, width=10)
start_button.pack(side=tk.LEFT, padx=20)

stop_button = tk.Button(button_frame, text="Stop Server", command=lambda: stop_server(), state=tk.DISABLED, height=2, width=10)
stop_button.pack(side=tk.LEFT, padx=20)

restart_button = tk.Button(button_frame, text="Restart Server", command=lambda: restart_server(), state=tk.DISABLED, height=2, width=12)
restart_button.pack(side=tk.LEFT, padx=20)

clear_button = tk.Button(button_frame, text="Clear Logs", command=lambda: clear_logs(), height=2, width=10)
clear_button.pack(side=tk.LEFT, padx=20)

# Setup logging configuration
def setup_logging():
    global logger
    logger = logging.getLogger('server')
    logger.setLevel(logging.INFO)

    # Create file and console handlers
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formatter for handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Initialize logging
setup_logging()

# Function for IP validation
def is_valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False
    
# Function for port validation
def is_valid_port(port):
    return 0 <= port <= 65535

# Function for chunk size validation
def is_valid_chunk_size(size):
    return size > 0

# Database initialization
def init_db():
    """Initializes the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        filename TEXT NOT NULL,
                        file_size INTEGER NOT NULL,
                        saved_path TEXT NOT NULL,
                        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      )''')
    conn.commit()
    conn.close()
    
# Function to log file to database
def log_file_to_db(filename, file_size, saved_path):
    """Logs file metadata to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (filename, file_size, saved_path) VALUES (?, ?, ?)",
                   (filename, file_size, saved_path))
    conn.commit()
    conn.close()
    
# Function to sanitize the filename to avoid "Directory Traversal attack"
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

# Function to handle client
def handle_client(client_socket, log_text, addr):
    global file_count_var, data_received_var

    try:
        # Receives data until the specified delimiter is found.
        def receive_until_delimiter(delimiter):
            data = b''
            while delimiter.encode() not in data:
                chunk = client_socket.recv(CHUNK_SIZE)
                if not chunk:
                    break
                data += chunk
            return data.decode()

        # Receive header data
        header_data = receive_until_delimiter(DELIMITER)
        if not header_data:
            logger.error(f"{'❌' * 10} Header data not received correctly.")
            log_text.insert(tk.END, f"{'❌' * 10} Header data not received correctly.\n")
            client_socket.sendall(b'error')  # Send error response
            return
        
        # Process metadata
        metadata = json.loads(header_data.split('\n', 1)[0])
        filename = sanitize_filename(metadata["filename"])
        file_size = metadata["file_size"]

        logger.info(f"📁 Received filename: {filename}\n📏 Expected file size: {file_size} bytes\n")
        log_text.insert(tk.END, f"📁 Received filename: {filename}\n📏 Expected file size: {file_size} bytes\n")

        # Ensure the bucket directory exists
        if not os.path.exists(BUCKET_DIR):
            os.makedirs(BUCKET_DIR, exist_ok=True)

        file_path = os.path.join(BUCKET_DIR, sanitize_filename(filename))
        logger.info(f"💾 Saving file to: {file_path}")
        log_text.insert(tk.END, f"💾 Saving file to: {file_path}\n")

        bytes_received = 0
        with open(file_path, 'wb') as f:
            while bytes_received < file_size:
                chunk = client_socket.recv(CHUNK_SIZE)
                if not chunk:
                    break
                f.write(chunk)
                bytes_received += len(chunk)
                data_received_var.set(data_received_var.get() + len(chunk))

        if bytes_received == file_size:
            logger.info(f"✅ File received successfully: {filename}")
            log_text.insert(tk.END, f"✅ File received successfully: {filename}\n")
            file_count_var.set(file_count_var.get() + 1)
            log_file_to_db(filename, file_size, file_path)
            client_socket.sendall(b'ok')  # Send success response
        else:
            logger.error(f"{'⚠️' * 5} File transfer incomplete: {filename}")
            log_text.insert(tk.END, f"{'⚠️' * 5} File transfer incomplete: {filename}\n")
            client_socket.sendall(b'error')

    except Exception as e:
        logger.error(f"{'❗' * 5} Error handling client: {e}")
        log_text.insert(tk.END, f"{'❗' * 5} Error handling client: {e}\n")
        client_socket.sendall(b'error')
    finally:
        client_socket.close()
        connections.remove(client_socket)
        logger.info(f"✅ Connection with {addr} is clossed!\n")
        log_text.insert(tk.END, f"✅ Connection with {addr} is clossed!\n")
        connection_count_var.set(len(connections))

# Function to log the session summar from start to stop of server
def log_session_summary():
    session_table = (
        "✨📊  Session Summary  📊✨\n"
        f"{'=' * 46}\n"
        "| Parameter               | Value         |\n"
        f"{'=' * 46}\n"
        f"| 📁 Files Processed      | {str(file_count_var.get()).ljust(14)}|\n"
        f"| 🗂 Data Received (bytes) | {str(data_received_var.get()).ljust(14)}|\n"
        f"| 🔄 Chunk Size (bytes)   | {str(chunk_size_var.get()).ljust(14)}|\n"
        f"{'=' * 46}\n"
        f"🔚 {'=' * 42} 🔚\n"
    )

    # Log the session summary
    logger.info(session_table)

    # Insert into the tkinter log text box
    log_text.insert(tk.END, session_table + "\n")
    log_text.yview(tk.END)

# Function to Log Settings when settings applied
def log_settings_summary(ip, port, chunk_size, bucket_dir):
    settings_table = (
        "⚙️  Settings applied:\n"
        "----------------------------------------------\n"
        "| Parameter   | Value                        |\n"
        "----------------------------------------------\n"
        f"| IP Address  | {str(ip).ljust(28)}|\n"
        f"| Port        | {str(port).ljust(28)}|\n"
        f"| Chunk Size  | {str(chunk_size).ljust(28)}|\n"
        f"| Directory   | {bucket_dir.ljust(28)}|\n"
        "----------------------------------------------\n"
    )

    logger.info(settings_table)
    log_text.insert(tk.END, settings_table + "\n")
    log_text.yview(tk.END)
    
# Function to Log a separator for better UI
def log_separator(context):
    separator = (
        f"\n🟡 <{'-' * 25} {context} {'-' * 25}> 🟡\n"
    )
    logger.info(separator)
    log_text.insert(tk.END, separator)
    log_text.yview(tk.END)

# Function to start the server
def start_server():
    global server_running, server_socket
    if not server_running:
        ip = server_ip_var.get()
        port = server_port_var.get()

        if not is_valid_ip(ip) or not is_valid_port(port):
            messagebox.showerror("❌ Invalid Configuration", "Please enter a valid IP address and port.")
            return

        chunk_size = chunk_size_var.get()
        if not is_valid_chunk_size(chunk_size):
            messagebox.showerror("❌ Invalid Configuration", "Please enter a valid chunk size.")
            return

        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((ip, port))
            server_socket.listen(5)
            server_running = True
            stop_event.clear()

            file_count_var.set(0)
            data_received_var.set(0)
            
            start_button.config(state=tk.DISABLED)
            stop_button.config(state=tk.NORMAL)
            restart_button.config(state=tk.NORMAL)

            Thread(target=accept_connections, daemon=True).start()
            logger.info(f"|{'=' * 20 } 🚀 Server started on {ip}:{port} {'=' * 20 }|")
            log_text.insert(tk.END, f"|{'=' * 20 } 🚀 Server started on {ip}:{port} {'=' * 20 }|\n")
            
        except socket.error as e:
            if e.errno == 10048:
                logger.error(f"⚠️ Port {port} is already in use.")
                log_text.insert(tk.END, f"⚠️ Port {port} is already in use.\n")
                messagebox.showerror("⚠️ Port Error", f"Port {port} is already in use.")
            else:
                logger.error(f"❌ Failed to start server: {e}")
                log_text.insert(tk.END, f"❌ Failed to start server: {e}\n")
    else:
        logger.warning(f"⚠️ Server is already running.")
        log_text.insert(tk.END, f"⚠️ Server is already running.\n")

# Function for accepting the clients connections
def accept_connections():
    while not stop_event.is_set():
        try:
            client_socket, addr = server_socket.accept()
            connections.append(client_socket)
            connection_count_var.set(len(connections))
            logger.info(f"{' ' * 5}> 🔗 Accepted connection from {addr}")
            log_text.insert(tk.END, f"{' ' * 5}> 🔗 Accepted connection from {addr}\n")
            Thread(target=handle_client, args=(client_socket, log_text, addr), daemon=True).start()
        except Exception as e:
            if not stop_event.is_set():
                logger.error(f"❌ Error accepting connections: {e}")
                log_text.insert(tk.END, f"❌ Error accepting connections: {e}\n")
            break

# Function to stop the server
def stop_server():
    global server_running, stop_event, server_socket

    if not server_running:
        messagebox.showwarning("⚠️ Server not running", "The server is not currently running.")
        return

    server_running = False
    stop_event.set()

    for conn in connections:
        conn.close()
        
    connections.clear()
    connection_count_var.set(0)

    stop_button.config(state=tk.DISABLED)
    start_button.config(state=tk.NORMAL)
    restart_button.config(state=tk.DISABLED)

    root.after(500, check_server_stopped)

# Function to check server status
def check_server_stopped():
    global server_socket
    try:
        if server_socket:
            server_socket.close()
            server_socket = None
        logger.info("🛑 Server stopped successfully.")
        log_text.insert(tk.END, "🛑  Server stopped successfully.\n")
        log_session_summary()
    except Exception as e:
        logger.error(f"❌ Error stopping the server: {e}")
        log_text.insert(tk.END, f"❌ Error stopping the server: {e}\n")

# Function to restart the server
def restart_server():
    log_separator("Server Restart")
    log_text.insert(tk.END, "🔄 Restarting the server...\n")
    log_text.yview(tk.END)
    stop_server()
    root.after(1000, start_server)
    
# Function to clear the logs
def clear_logs():
    log_text.delete('1.0', tk.END)

def on_closing():
    if server_running:
        messagebox.showinfo("Quit", "The server is still running. Please stop it first.")
    else:
        root.destroy()
 
# Apply settings function       
def apply_settings():
    global SERVER_IP, SERVER_PORT, CHUNK_SIZE, BUCKET_DIR
    
    new_ip = server_ip_var.get()
    new_port = server_port_var.get()
    new_chunk_size = chunk_size_var.get()
    new_dir = directory_var.get()
    
    if not is_valid_ip(new_ip):
        messagebox.showerror("Invalid IP", "The provided IP address is invalid.")
        return

    if not is_valid_port(new_port):
        messagebox.showerror("Invalid Port", "The provided port number is invalid. It must be between 0 and 65535.")
        return

    if not is_valid_chunk_size(new_chunk_size):
        messagebox.showerror("Invalid Chunk Size", "The chunk size must be a positive integer.")
        return

    SERVER_IP = new_ip
    SERVER_PORT = new_port
    CHUNK_SIZE = new_chunk_size
    BUCKET_DIR = new_dir
    
    if not os.path.exists(BUCKET_DIR):
        os.makedirs(BUCKET_DIR, exist_ok=True)
        logger.info(f"📂 Storage directory created: {BUCKET_DIR}")
        log_text.insert(tk.END, f"📂 Storage directory created: {BUCKET_DIR}\n")
        
    messagebox.showinfo("Settings", "Settings updated successfully.")
    
    log_settings_summary(new_ip,new_port,new_chunk_size,new_dir)

    if server_running:
        restart_server()
        
# Initialize the database
init_db()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the Tkinter main loop
root.mainloop()