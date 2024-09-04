import socket
import os
import json
from threading import Thread, Event
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import logging
import sqlite3

# Constants
SERVER_IP = '0.0.0.0'
SERVER_PORT = 5000
BUCKET_DIR = 'bucket_storage'
DELIMITER = "---END-HEADER---"
CHUNK_SIZE = 4096
DB_FILE = 'server_data.db'

# Create the bucket storage directory if it doesn't exist
os.makedirs(BUCKET_DIR, exist_ok=True)

# Server control flags
server_running = False
stop_event = Event()
connections = []  # Track active connections

# Initialize the Tkinter root window
root = tk.Tk()
root.title("Server Application")
root.geometry("800x600")
root.minsize(800, 600)

# Tkinter variables
connection_count_var = tk.IntVar(value=0)
file_count_var = tk.IntVar(value=0)
data_received_var = tk.IntVar(value=0)
chunk_size_var = tk.IntVar(value=CHUNK_SIZE)
server_ip_var = tk.StringVar(value=SERVER_IP)
server_port_var = tk.IntVar(value=SERVER_PORT)

style = ttk.Style()
style.configure("TNotebook.Tab", padding=[20, 10])

# Create a notebook with tabs
notebook = ttk.Notebook(root)
notebook.pack(pady=20, expand=True, fill="both")

# Add padding to the tabs
style = ttk.Style()
style.configure("TNotebook.Tab", padding=[20, 10])

# Create a frame for the log
log_frame = tk.Frame(notebook)
notebook.add(log_frame, text="Logs")

# Create a frame for the status
status_frame = tk.Frame(notebook)
notebook.add(status_frame, text="Status")

# Create a frame for the settings
settings_frame = tk.Frame(notebook)
notebook.add(settings_frame, text="Settings")

# Create and pack the log text area
log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=20, width=90)
log_text.pack(pady=20)

# Create and pack the status frame
status_frame.grid_columnconfigure(0, weight=1)
status_frame.grid_columnconfigure(1, weight=1)
tk.Label(status_frame, text="Active Connections:").grid(row=0, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=connection_count_var).grid(row=0, column=1, padx=20, pady=10)

tk.Label(status_frame, text="Files Processed:").grid(row=1, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=file_count_var).grid(row=1, column=1, padx=20, pady=10)

tk.Label(status_frame, text="Data Received (bytes):").grid(row=2, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=data_received_var).grid(row=2, column=1, padx=20, pady=10)

tk.Label(status_frame, text="Chunk Size (bytes):").grid(row=3, column=0, padx=20, pady=10)
tk.Label(status_frame, textvariable=chunk_size_var).grid(row=3, column=1, padx=20, pady=10)

# Create and pack the settings frame
settings_frame.grid_columnconfigure(0, weight=1)
settings_frame.grid_columnconfigure(1, weight=1)
tk.Label(settings_frame, text="Server IP:").grid(row=0, column=0, padx=20, pady=10)
server_ip_entry = tk.Entry(settings_frame, textvariable=server_ip_var)
server_ip_entry.grid(row=0, column=1, padx=20, pady=10)

tk.Label(settings_frame, text="Port:").grid(row=1, column=0, padx=20, pady=10)
server_port_entry = tk.Entry(settings_frame, textvariable=server_port_var)
server_port_entry.grid(row=1, column=1, padx=20, pady=10)

tk.Label(settings_frame, text="Chunk Size:").grid(row=2, column=0, padx=20, pady=10)
chunk_size_entry = tk.Entry(settings_frame, textvariable=chunk_size_var)
chunk_size_entry.grid(row=2, column=1, padx=20, pady=10)

apply_button = tk.Button(settings_frame, text="Apply", command=lambda: apply_settings(), height=2, width=10)
apply_button.grid(row=3, column=0, columnspan=2, padx=20, pady=20)

# Create and pack the button frame
button_frame = tk.Frame(root)
button_frame.pack(pady=20)

start_button = tk.Button(button_frame, text="Start Server", command=lambda: start_server(), height=2, width=10)
start_button.pack(side=tk.LEFT, padx=20)

stop_button = tk.Button(button_frame, text="Stop Server", command=lambda: stop_server(), state=tk.DISABLED, height=2, width=10)
stop_button.pack(side=tk.LEFT, padx=20)

restart_button = tk.Button(button_frame, text="Restart Server", command=lambda: restart_server(), state=tk.DISABLED, height=2, width=10)
restart_button.pack(side=tk.LEFT, padx=20)

clear_button = tk.Button(button_frame, text="Clear Logs", command=lambda: clear_logs(), height=2, width=10)
clear_button.pack(side=tk.LEFT, padx=20)

# Create a logger
logger = logging.getLogger('server')
logger.setLevel(logging.INFO)

# Create a file handler
file_handler = logging.FileHandler('server.log')
file_handler.setLevel(logging.INFO)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def is_valid_ip(ip):
    """Validates if the provided IP address is valid."""
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def is_valid_port(port):
    """Validates if the provided port number is within the valid range."""
    return 0 <= port <= 65535

def is_valid_chunk_size(size):
    """Validates if the provided chunk size is a positive integer."""
    return size > 0

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

def log_file_to_db(filename, file_size, saved_path):
    """Logs file metadata to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (filename, file_size, saved_path) VALUES (?, ?, ?)",
                   (filename, file_size, saved_path))
    conn.commit()
    conn.close()

def handle_client(client_socket, log_text, addr):
    """Handles communication with a client."""
    global file_count_var, data_received_var
    try:
        def receive_until_delimiter(delimiter):
            """Receives data until the specified delimiter is found."""
            data = b''
            while delimiter.encode() not in data:
                chunk = client_socket.recv(CHUNK_SIZE)
                if not chunk:
                    break
                data += chunk
            return data.decode()

        header_data = receive_until_delimiter(DELIMITER)
        if not header_data:
            logger.error("Header data not received correctly.")
            log_text.insert(tk.END, "Header data not received correctly.\n")
            client_socket.sendall(b'error')  # Send error response
            return
        
        metadata = json.loads(header_data.split('\n', 1)[0])
        filename = metadata["filename"]
        file_size = metadata["file_size"]

        logger.info(f"Received filename: {filename}")
        logger.info(f"Expected file size: {file_size} bytes")
        log_text.insert(tk.END, f"Received filename: {filename}\n")
        log_text.insert(tk.END, f"Expected file size: {file_size} bytes\n")

        file_path = os.path.join(BUCKET_DIR, filename)
        logger.info(f"Saving file to: {file_path}")
        log_text.insert(tk.END, f"Saving file to: {file_path}\n")

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
            logger.info(f"File received successfully: {filename}")
            log_text.insert(tk.END, f"File received successfully: {filename}\n")
            file_count_var.set(file_count_var.get() + 1)
            log_file_to_db(filename, file_size, file_path)
            client_socket.sendall(b'success')  # Send success response
        else:
            logger.error(f"File transfer incomplete: {filename}")
            log_text.insert(tk.END, f"File transfer incomplete: {filename}\n")
            client_socket.sendall(b'error')  # Send error response

    except Exception as e:
        logger.error(f"Error handling client: {e}")
        log_text.insert(tk.END, f"Error handling client: {e}\n")
        client_socket.sendall(b'error')  # Send error response
    finally:
        client_socket.close()
        connections.remove(client_socket)
        connection_count_var.set(len(connections))

def log_separator(context):
    """Logs a separator for better navigation within the log file."""
    separator = f"<===================== {context} ===========================>"
    logger.info(separator)
    
def start_server():
    """Starts the server."""
    global server_running, server_socket
    if not server_running:
        ip = server_ip_var.get()
        port = server_port_var.get()

        if not is_valid_ip(ip) or not is_valid_port(port):
            messagebox.showerror("Invalid Configuration", "Please enter a valid IP address and port.")
            return

        chunk_size = chunk_size_var.get()
        if not is_valid_chunk_size(chunk_size):
            messagebox.showerror("Invalid Configuration", "Please enter a valid chunk size.")
            return

        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((ip, port))
            server_socket.listen(5)
            server_running = True
            stop_event.clear()

            start_button.config(state=tk.DISABLED)
            stop_button.config(state=tk.NORMAL)
            restart_button.config(state=tk.NORMAL)

            Thread(target=accept_connections, daemon=True).start()
            logger.info(f"Server started on {ip}:{port}")
            log_text.insert(tk.END, f"Server started on {ip}:{port}\n")
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            log_text.insert(tk.END, f"Failed to start server: {e}\n")
    else:
        logger.warning("Server is already running.")
        log_text.insert(tk.END, "Server is already running.\n")

def accept_connections():
    """Accepts incoming client connections."""
    while not stop_event.is_set():
        try:
            client_socket, addr = server_socket.accept()
            connections.append(client_socket)
            connection_count_var.set(len(connections))
            logger.info(f"Accepted connection from {addr}")
            log_text.insert(tk.END, f"Accepted connection from {addr}\n")
            Thread(target=handle_client, args=(client_socket, log_text, addr), daemon=True).start()
        except Exception as e:
            if not stop_event.is_set():
                logger.error(f"Error accepting connections: {e}")
                log_text.insert(tk.END, f"Error accepting connections: {e}\n")
            break

def stop_server():
    """Stops the server."""
    global server_running, stop_event
    if not server_running:
        messagebox.showwarning("Server not running", "The server is not currently running.")
        return

    stop_event.set()
    server_running = False
    for conn in connections:
        conn.close()
    connections.clear()
    connection_count_var.set(0)
    stop_button.config(state=tk.DISABLED)
    start_button.config(state=tk.NORMAL)
    restart_button.config(state=tk.DISABLED)
    
    logger.info(f"\n{'='*20} SESSION END {'='*20}\n")
    log_text.insert(tk.END, f"\n{'='*20} SESSION END {'='*20}\n")
    
    logger.info("Server stopped successfully.")
    log_text.insert(tk.END, "Server stopped successfully.\n")

def restart_server():
    """Restarts the server."""
    log_separator("Server Restart")
    log_text.insert(tk.END, "Restarting the server...\n")
    log_text.yview(tk.END)
    stop_server()
    start_server()

def clear_logs():
    """Clears the log display."""
    log_text.delete('1.0', tk.END)

def on_closing():
    """Handles the window close event."""
    if server_running:
        if messagebox.askokcancel("Quit", "The server is still running. Do you want to stop the server and exit?"):
            stop_server()  # Stop the server before closing the application
            root.destroy()
    else:
        root.destroy()
        
def apply_settings():
    """Applies settings changes."""
    global CHUNK_SIZE
    ip = server_ip_var.get()
    port = server_port_var.get()
    chunk_size = chunk_size_var.get()

    if not is_valid_ip(ip):
        messagebox.showerror("Invalid IP", "The provided IP address is invalid.")
        return

    if not is_valid_port(port):
        messagebox.showerror("Invalid Port", "The provided port number is invalid. It must be between 0 and 65535.")
        return

    if not is_valid_chunk_size(chunk_size):
        messagebox.showerror("Invalid Chunk Size", "The chunk size must be a positive integer.")
        return

    CHUNK_SIZE = chunk_size
    restart_server()
    messagebox.showinfo("Settings", "Settings updated successfully.")

# Initialize the database
init_db()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the Tkinter main loop
root.mainloop()