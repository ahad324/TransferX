import socket, sqlite3, re, os, sys, logging, json, io
from pathlib import Path
from threading import Thread, Event
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, font, Label, Frame

import mdns_connect
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
    if not os.path.exists(BUCKET_DIR):
        os.makedirs(BUCKET_DIR, exist_ok=True)
        logger.info(f"📂 Storage directory created: {BUCKET_DIR}")
        append_log(f"📂 Storage directory created: {BUCKET_DIR}")

# Constants
SERVER_IP = '0.0.0.0'
SERVER_PORT = 5000
CHUNK_SIZE = 8192
DELIMITER = "---END-HEADER---"
DB_FILE = os.path.join(BASE_DIR, 'server_data.db')
LOG_FILE = os.path.join(BASE_DIR, 'server.log')
BUCKET_DIR = os.path.join(BASE_DIR, 'bucket_storage')
FONT = "Segoe UI"

# Define colors
DARK_BG_COLOR = '#161718'
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

# Functions to append text to mdns and Logs
def append_mdns_log(message):
    def update_log():
        mdns_log_text.insert(tk.END, message + "\n")
        mdns_log_text.yview(tk.END)
    root.after(0, update_log)
def append_log(message):
    log_text.insert(tk.END,message+"\n")
    log_text.yview(tk.END)
    
# Initialize the Tkinter root window
root = tk.Tk()
root.title("TransferX Server Panel")
root.geometry("800x630")
root.minsize(300, 300)
set_window_icon(root)
root.configure(bg=DARK_BG_COLOR)
root.option_add("*Font", font.Font(family=FONT)) # Apply the font globally

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
style.configure("TNotebook.Tab", padding=[20, 10],font=(FONT,12,"bold"))

# Create a notebook with tabs
notebook = ttk.Notebook(root)
notebook.pack(pady=20, expand=True, fill="both")

# Frames for notebook tabs
log_frame = tk.Frame(notebook,padx=20)
log_frame.pack(fill=tk.BOTH, expand=True)
notebook.add(log_frame, text="Logs")

mdns_log_frame = tk.Frame(notebook, padx=20)
mdns_log_frame.pack(fill=tk.BOTH, expand=True)
notebook.add(mdns_log_frame, text="MDNS Logs")

status_frame = tk.Frame(notebook)
notebook.add(status_frame, text="Status")

settings_frame = tk.Frame(notebook)
notebook.add(settings_frame, text="Settings")

# Create and pack the log text area
log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,bg=LIGHT_BG_COLOR,height=20,font=("Courier",10))
log_text.grid(row=0, column=0, sticky='nsew')
log_frame.grid_rowconfigure(0, weight=1)
log_frame.grid_columnconfigure(0, weight=1)
append_log("CLICK ON THE START SERVER BUTTON...")

# Create and pack the mdns log text area
mdns_log_text = scrolledtext.ScrolledText(mdns_log_frame, wrap=tk.WORD, bg=LIGHT_BG_COLOR, height=20, font=("Courier", 10))
mdns_log_text.grid(row=0, column=0, sticky='nsew')
mdns_log_frame.grid_rowconfigure(0, weight=1)
mdns_log_frame.grid_columnconfigure(0, weight=1)
append_mdns_log("MDNS Connection logs will appear here...")

# Status frame content
status_frame.grid_columnconfigure(0, weight=1)
status_frame.grid_columnconfigure(1, weight=1)
def create_status_label(frame, text, variable, row):
    tk.Label(frame, text=text, font=(FONT, 12, "bold")).grid(row=row, column=0, padx=20, pady=10)
    tk.Label(frame, textvariable=variable).grid(row=row, column=1, padx=20, pady=10)
# Define labels
status_labels = [
    ("Active Connections:", connection_count_var),
    ("Files Processed:", file_count_var),
    ("Data Received (bytes):", data_received_var),
    ("Chunk Size (bytes):", chunk_size_var)
]

# Create labels
for i, (text, var) in enumerate(status_labels):
    create_status_label(status_frame, text, var, i)

# Settings frame content
settings_frame.grid_columnconfigure(0, weight=1)
settings_frame.grid_columnconfigure(1, weight=2)

def create_label_entry(frame, label_text, text_variable, row, font=(FONT, 12, "bold"), entry_width=30):
    tk.Label(frame, text=label_text, anchor="e", font=font).grid(row=row, column=0, padx=20, pady=10, sticky="e")
    entry = tk.Entry(frame, textvariable=text_variable, font=(FONT, 12), width=entry_width)
    entry.config(relief="solid", borderwidth=1)
    entry.grid(row=row, column=1, padx=20, pady=10, ipady=4, sticky="ew")  # Increase internal padding and make it expandable
    return entry

# Create label-entry pairs
entry_widgets = [
    ("Server IP:", server_ip_var, 0),
    ("Port:", server_port_var, 1),
    ("Chunk Size:", chunk_size_var, 2),
    ("Storage Directory:", directory_var, 3)
]

# Create labels and entries
for label_text, text_var, row in entry_widgets:
    create_label_entry(settings_frame, label_text, text_var, row)

# Make the second column expandable
settings_frame.grid_columnconfigure(1, weight=1)


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

    # Ensure the log directory exists
    log_dir = os.path.dirname(LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
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

    def receive_until_delimiter(delimiter):
        data = b''
        while delimiter.encode('utf-8') not in data:
            chunk = client_socket.recv(CHUNK_SIZE)
            if not chunk:
                break
            data += chunk
        return data

    def get_unique_filename(file_path):
        base, extension = os.path.splitext(file_path)
        counter = 1
        new_file_path = file_path
        while os.path.exists(new_file_path):
            new_file_path = f"{base}({counter}){extension}"
            counter += 1
        return new_file_path
    
    def get_file_size(file_path):
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0

    try:
        # Receive header data
        header_data = receive_until_delimiter(DELIMITER)
        if not header_data:
            logger.error("❌ Header data not received.This might be a discovery request.")
            append_log("❌ Header data not received.This might be a discovery request.")
            client_socket.sendall(b'Header data not received.')  # Send error response
            return

        # Try to decode header data with different encodings
        encodings = ['utf-8', 'iso-8859-1', 'windows-1252']
        header_str = None
        for encoding in encodings:
            try:
                header_str = header_data.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if header_str is None:
            logger.error(f"{'❌' * 10} Unable to decode header data.")
            append_log(f"{'❌' * 10} Unable to decode header data.")
            client_socket.sendall(b'Unable to decode header data.')  # Send error response
            return

        # Process metadata
        try:
            metadata = json.loads(header_str.split('\n', 1)[0])
            filename = sanitize_filename(metadata["filename"])
            file_size = metadata["file_size"]
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"{'❌' * 10} Error processing metadata: {e}")
            append_log(f"{'❌' * 10} Error processing metadata: {e}")
            client_socket.sendall(b'Error processing metadata.')  # Send error response
            return


        # Ensure the bucket directory exists
        if not os.path.exists(BUCKET_DIR):
            ensure_base_dir_exists()

        file_path = os.path.join(BUCKET_DIR, sanitize_filename(filename))
        file_path = get_unique_filename(file_path)  # Ensure unique filename
        logger.info(f"💾 Saving file to: {file_path}")
        append_log(f"💾 Saving file to: {file_path}")
        
        # Check if the file already exists and get its size
        bytes_received = get_file_size(file_path)
        client_socket.sendall(f"{bytes_received}".encode('utf-8'))  # Send the current size to the client
        try:
            with open(file_path, 'wb') as f:
                while bytes_received < file_size:
                    chunk = client_socket.recv(min(CHUNK_SIZE, file_size - bytes_received))
                    if not chunk:
                        break
                    f.write(chunk)
                    bytes_received += len(chunk)
                    data_received_var.set(data_received_var.get() + len(chunk))

            if bytes_received == file_size:
                logger.info(f"✅ File received successfully: {filename}")
                append_log(f"✅ File received successfully: {filename}")
                file_count_var.set(file_count_var.get() + 1)
                log_file_to_db(filename, file_size, file_path)
                client_socket.sendall(b'ok\n')  # Send success response
            else:
                logger.warning(f"⚠️ File transfer incomplete: {filename}. Expected {file_size} bytes, received {bytes_received} bytes.")
                append_log(f"⚠️ File transfer incomplete: {filename}. Expected {file_size} bytes, received {bytes_received} bytes.")
                client_socket.sendall(b'File transfer incomplete.\n')
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            logger.error(f"{'⚠️' * 5} Error during file transfer: {str(e)}")
            append_log(f"{'⚠️' * 5} Error during file transfer: {str(e)}")
            client_socket.sendall(b'Error during file transfer.\n')
            
    except Exception as e:
        logger.error(f"{'❗' * 5} Error handling client: {str(e)}")
        append_log(f"{'❗' * 5} Error handling client: {str(e)}")
        client_socket.sendall(b'Error handling client.')
    finally:
        client_socket.close()
        connections.remove(client_socket)
        logger.info(f"✅ Connection with {addr} is closed!")
        append_log(f"✅ Connection with {addr} is closed!")
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
    append_log(session_table)

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
    append_log(settings_table)
    
# Function to Log a separator for better UI
def log_separator(context):
    separator = (
        f"\n🟡 <{'-' * 25} {context} {'-' * 25}> 🟡\n"
    )
    logger.info(separator)
    append_log(separator)

# Function to start the server
def start_server():
    global server_running, server_socket, zeroconf, mdns_info, mdns_browser
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
            logger.info(f"|{'=' * 20 } 📡 Server started on {ip}:{port} {'=' * 20 }|")
            append_log(f"|{'=' * 20 } 📡 Server started on {ip}:{port} {'=' * 20 }|")
            # Start the mDNS server
            zeroconf, mdns_info, mdns_browser = mdns_connect.start_mdns_listener(BASE_DIR, append_mdns_log, port)
            
        except socket.error as e:
            if e.errno == 10048:
                logger.error(f"⚠️ Port {port} is already in use.")
                append_log( f"⚠️ Port {port} is already in use.")
                messagebox.showerror("⚠️ Port Error", f"Port {port} is already in use.")
            else:
                logger.error(f"❌ Failed to start server: {e}")
                append_log(f"❌ Failed to start server: {e}")
    else:
        logger.warning(f"⚠️ Server is already running.")
        append_log(f"⚠️ Server is already running.")

# Function for accepting the clients connections
def accept_connections():
    while not stop_event.is_set():
        try:
            client_socket, addr = server_socket.accept()
            connections.append(client_socket)
            connection_count_var.set(len(connections))
            logger.info(f"{'  ' * 5} 🔗 Accepted connection from {addr}")
            append_log(f"{'  ' * 5} 🔗 Accepted connection from {addr}")
            Thread(target=handle_client, args=(client_socket, log_text, addr), daemon=True).start()
        except Exception as e:
            if not stop_event.is_set():
                logger.error(f"❌ Error accepting connections: {e}")
                append_log(f"❌ Error accepting connections: {e}")
            break

# Function to stop the server
def stop_server():
    global server_running, stop_event, server_socket

    if not server_running:
        messagebox.showwarning("⚠️ Server not running", "The server is not currently running.")
        return
    # Stop the mDNS server
    mdns_connect.stop_mdns_listener(zeroconf, mdns_info,mdns_browser)
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
        logger.info("🛑 Server stopped.")
        append_log("🛑  Server stopped.")
        log_session_summary()
    except Exception as e:
        logger.error(f"❌ Error stopping the server: {e}")
        append_log(f"❌ Error stopping the server: {e}")

# Function to restart the server
def restart_server():
    log_separator("Server Restart")
    append_log("🔄 Restarting the server...")
    stop_server()
    root.after(1000, start_server)
    
# Function to clear the logs
def clear_logs():
    log_text.delete('1.0', tk.END)
    mdns_log_text.delete('1.0',tk.END)

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
    
    ensure_base_dir_exists()
        
    messagebox.showinfo("Settings", "Settings updated successfully.")
    
    log_settings_summary(new_ip,new_port,new_chunk_size,new_dir)

    if server_running:
        restart_server()
        
# Initialize the database
init_db()
# Create the base directory if it doesn't exist
ensure_base_dir_exists()

root.protocol("WM_DELETE_WINDOW", on_closing)
# Create bottom frame
from developer_label import create_developer_label
bottom_frame = Frame(root, bg=DARK_BG_COLOR)
bottom_frame.pack(side='bottom', fill='x', padx=5, pady=5)

# Create a frame for the version label and website link
website_frame = Frame(bottom_frame, bg=DARK_BG_COLOR)
website_frame.pack(side='left')

# Official Website Label
official_website_label = Label(website_frame, text="Official Website:", font=(FONT, 12, "italic","bold"), bg=DARK_BG_COLOR, fg="white")
official_website_label.pack(side='left')

# Clickable Website Link
website_link = Label(website_frame, text="transferx.netlify.app", font=(FONT, 12, "italic","underline"), bg=DARK_BG_COLOR, fg="white", cursor="hand2")
website_link.pack(side='left')

# Function to open the website
def open_website(event):
    import webbrowser
    webbrowser.open("https://transferx.netlify.app/")

# Bind the click event to the website link
website_link.bind("<Button-1>", open_website)


# Import and use the DeveloperLabel class
from developer_label import create_developer_label

# Create developer label (right side)
developer_label = create_developer_label(
    bottom_frame,
    FONT,
    light_theme={'bg': DARK_BG_COLOR, 'fg': 'white'},
    dark_theme={'bg': DARK_BG_COLOR, 'fg': 'white'}
)
# Run the Tkinter main loop
root.mainloop()