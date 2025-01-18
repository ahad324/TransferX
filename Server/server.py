import sqlite3
import os
import sys
from pathlib import Path
from utility import get_downloads_folder, ensure_base_dir_exists, sanitize_filename, format_size, is_valid_ip, is_valid_port, is_valid_chunk_size, set_window_icon
from threading import Thread, Event
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, font, Label, Frame

import mdns_connect
import updater

class TransferXServer:
    # Constants
    DELIMITER = "---END-HEADER---"
    FONT = "Poppins"
    DARK_COLOR = '#111827'
    LIGHT_COLOR = '#f9fafb'
    BUTTON_CONFIG = {
        'height': 1,
        'width': 15,
        'borderwidth': 2,
        'padx': 10,
        'pady': 5,
        'cursor': "hand2",
        'font': (FONT, 12)
    }

    def __init__(self):
        self.init_paths()
        self.setup_logging()
        self.init_db()
        self.server_running = False
        self.stop_event = Event()
        self.connections = set()
        self.setup_gui()

    def init_paths(self):
        if getattr(sys, 'frozen', False):
            self.current_dir = Path(sys._MEIPASS)
            self.base_dir = get_downloads_folder() / 'TransferX Server'
        else:
            self.current_dir = Path(__file__).parent
            self.base_dir = self.current_dir

        self.db_file = os.path.join(self.base_dir, 'server_data.db')
        self.log_file = os.path.join(self.base_dir, 'server.log')
        self.bucket_dir = os.path.join(self.base_dir, 'bucket_storage')

    def setup_logging(self):
        import logging
        self.logger = logging.getLogger('server')
        self.logger.setLevel(logging.INFO)

        log_dir = os.path.dirname(self.log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def init_db(self):
        ensure_base_dir_exists(self.base_dir)
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            filename TEXT NOT NULL,
                            file_size INTEGER NOT NULL,
                            saved_path TEXT NOT NULL,
                            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            address TEXT NOT NULL
                            )''')
        conn.commit()
        conn.close()

    def log_file_to_db(self, filename, file_size, saved_path, address):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO files (filename, file_size, saved_path, address) VALUES (?, ?, ?, ?)",
                        (filename, file_size, saved_path, address))
        conn.commit()
        conn.close()

    def setup_gui(self):
        self.root_window_minsize = (900, 650)
        self.root = tk.Tk()
        self.root.title("TransferX Server Panel")
        self.root.state('zoomed')
        self.root.minsize(self.root_window_minsize[0],self.root_window_minsize[1])
        set_window_icon(self.root)
        self.root.configure(bg=self.DARK_COLOR)
        self.root.option_add("*Font", font.Font(family=self.FONT))
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[20, 10], font=(self.FONT, 12, "bold"))

        self.connection_count_var = tk.IntVar(value=0)
        self.file_count_var = tk.IntVar(value=0)
        self.data_received_var = tk.IntVar(value=0)
        self.chunk_size_var = tk.IntVar(value=8192)
        self.server_ip_var = tk.StringVar(value="0.0.0.0")
        self.server_port_var = tk.IntVar(value=5000)
        self.allowed_extensions_var = tk.StringVar(value=".txt,.jpg,.png,.pdf,.zip")
        self.max_file_size_var = tk.IntVar(value=10)
        self.directory_var = tk.StringVar(value=self.bucket_dir + "/")

        self.create_notebook()
        self.create_buttons()
        self.create_bottom_frame()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_bottom_frame(self):
        # Create bottom frame
        from developer_label import create_developer_label
        bottom_frame = Frame(self.root, bg=self.DARK_COLOR)
        bottom_frame.pack(side='bottom', fill='x', padx=5, pady=5)

        # Create a frame for the version label and website link
        website_frame = Frame(bottom_frame, bg=self.DARK_COLOR)
        website_frame.pack(side='left')

        # Official Website Label
        official_website_label = Label(
            website_frame, 
            text="Official Website:", 
            font=(self.FONT, 12, "bold"), 
            bg=self.DARK_COLOR, 
            fg=self.LIGHT_COLOR
        )
        official_website_label.pack(side='left')

        # Clickable Website Link
        website_link = Label(
            website_frame, 
            text="transferx.netlify.app", 
            font=(self.FONT, 12, "italic", "underline"), 
            bg=self.DARK_COLOR, 
            fg=self.LIGHT_COLOR, 
            cursor="hand2"
        )
        website_link.pack(side='left')

        # Bind the click event to the website link
        website_link.bind("<Button-1>", self.open_website)

        # Centered Version Label
        self.version_label = Label(
            bottom_frame, 
            text=f"version {updater.AppVersion}",
            font=(self.FONT, 12, "italic"),
            bg=self.DARK_COLOR, 
            fg=self.LIGHT_COLOR
        )
        self.version_label.pack(side='left', padx=5, pady=5, expand=True)
        updater.set_version_label(self.version_label)

        # Create developer label (right side)
        self.developer_label = create_developer_label(
            bottom_frame,
            self.FONT,
            light_theme={'bg': self.DARK_COLOR, 'fg': self.LIGHT_COLOR},
            dark_theme={'bg': self.DARK_COLOR, 'fg': self.LIGHT_COLOR}
        )
        
    def open_website(self, event):
        import webbrowser
        webbrowser.open("https://transferx.netlify.app/")

    def create_notebook(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(pady=20, expand=True, fill="both")

        log_frame = self.create_log_frame(notebook)
        mdns_log_frame = self.create_mdns_log_frame(notebook)
        status_frame = self.create_status_frame(notebook)
        settings_frame = self.create_settings_frame(notebook)

        notebook.add(log_frame, text="Logs")
        notebook.add(mdns_log_frame, text="MDNS Logs")
        notebook.add(status_frame, text="Status")
        notebook.add(settings_frame, text="Settings")

    def create_log_frame(self, notebook):
        log_frame = tk.Frame(notebook, padx=20)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg=self.LIGHT_COLOR, height=20, font=("Courier", 10))
        self.log_text.grid(row=0, column=0, sticky='nsew')
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        self.append_log("CLICK ON THE START SERVER BUTTON...")
        return log_frame

    def create_mdns_log_frame(self, notebook):
        mdns_log_frame = tk.Frame(notebook, padx=20)
        mdns_log_frame.pack(fill=tk.BOTH, expand=True)

        self.mdns_log_text = scrolledtext.ScrolledText(mdns_log_frame, wrap=tk.WORD, bg=self.LIGHT_COLOR, height=20, font=("Courier", 10))
        self.mdns_log_text.grid(row=0, column=0, sticky='nsew')
        mdns_log_frame.grid_rowconfigure(0, weight=1)
        mdns_log_frame.grid_columnconfigure(0, weight=1)
        self.append_mdns_log("MDNS Connection logs will appear here...")
        return mdns_log_frame

    def create_status_frame(self, notebook):
        status_frame = tk.Frame(notebook)
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=1)

        status_labels = [
            ("Active Connections:", self.connection_count_var),
            ("Files Processed:", self.file_count_var),
            ("Data Received (bytes):", self.data_received_var),
            ("Chunk Size (bytes):", self.chunk_size_var)
        ]

        for i, (text, var) in enumerate(status_labels):
            tk.Label(status_frame, text=text, font=(self.FONT, 12, "bold")).grid(row=i, column=0, padx=20, pady=10)
            tk.Label(status_frame, textvariable=var).grid(row=i, column=1, padx=20, pady=10)
        

        return status_frame

    def create_settings_frame(self, notebook):
        settings_frame = tk.Frame(notebook)
        settings_frame.grid_columnconfigure(0, weight=1, uniform="settings")
        settings_frame.grid_columnconfigure(1, weight=2, uniform="settings")

        # Define all input fields in a single list
        entry_widgets = [
            ("Server IP:", self.server_ip_var, 0),
            ("Port:", self.server_port_var, 1),
            ("Chunk Size (bytes):", self.chunk_size_var, 2),
            ("Storage Directory:", self.directory_var, 3),
            ("Allowed Extensions (comma-separated):", self.allowed_extensions_var, 4),
            ("Max File Size (MB):", self.max_file_size_var, 5),
        ]

        # Dynamically create labels and entries for settings
        for label_text, text_var, row in entry_widgets:
            self.create_label_entry(settings_frame, label_text, text_var, row)
            
        # Add Apply button
        apply_button = tk.Button(
            settings_frame,
            text="Update Settings",
            command=self.apply_settings,
            bg="#4CAF50",  # Green background for Apply button
            fg=self.LIGHT_COLOR,  # White text
            activebackground="#45a049",  # Slightly darker green on hover
            activeforeground=self.LIGHT_COLOR,
            **self.BUTTON_CONFIG,
        )
        apply_button.grid(
            row=len(entry_widgets), column=0, columnspan=2, padx=20, pady=20, sticky="n"
        )

        return settings_frame

    def create_label_entry(self, frame, label_text, text_variable, row, font=None, entry_width=30):
        if font is None:
            font = (self.FONT, 12, "bold")

        # Label with consistent styling
        tk.Label(
            frame,
            text=label_text,
            font=font,
            anchor="e",
            fg=self.DARK_COLOR
        ).grid(row=row, column=0, padx=20, pady=10, sticky="e")

        # Entry with enhanced styling
        entry = tk.Entry(
            frame,
            textvariable=text_variable,
            font=(self.FONT, 12),
            width=entry_width,
            relief="solid",
            bg="#ffffff",  # White background
            fg="#000000",  # Black text
            insertbackground="#000000",  # Black cursor
        )
        entry.grid(row=row, column=1, padx=20, pady=10, ipady=4, sticky="ew")

        return entry

    def create_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.config(bg=self.DARK_COLOR)
        button_frame.pack(pady=20)

        self.start_button = tk.Button(button_frame, text="Start Server", command=self.start_server,**self.BUTTON_CONFIG)
        self.start_button.pack(side=tk.LEFT, padx=20)

        self.stop_button = tk.Button(button_frame, text="Stop Server", command=self.stop_server, state=tk.DISABLED,**self.BUTTON_CONFIG)
        self.stop_button.pack(side=tk.LEFT, padx=20)

        self.restart_button = tk.Button(button_frame, text="Restart Server", command=self.restart_server, state=tk.DISABLED,**self.BUTTON_CONFIG)
        self.restart_button.pack(side=tk.LEFT, padx=20)

        clear_button = tk.Button(button_frame, text="Clear Logs", command=self.clear_logs,**self.BUTTON_CONFIG)
        clear_button.pack(side=tk.LEFT, padx=20)

    def append_log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.yview(tk.END)

    def append_mdns_log(self, message):
        def update_log():
            self.mdns_log_text.insert(tk.END, message + "\n")
            self.mdns_log_text.yview(tk.END)
        self.root.after(0, update_log)

    def on_closing(self):
        if self.server_running:
            messagebox.showinfo("Quit", "The server is still running. Please stop it first.")
        else:
            self.root.destroy()

    def start_server(self):
        import socket
        if not self.server_running:
            ip = self.server_ip_var.get()
            port = self.server_port_var.get()

            if not is_valid_ip(ip) or not is_valid_port(port):
                messagebox.showerror("❌ Invalid Configuration", "Please enter a valid IP address and port.")
                return

            if not is_valid_chunk_size(self.chunk_size_var.get()):
                messagebox.showerror("❌ Invalid Configuration", "Please enter a valid chunk size.")
                return

            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind((ip, port))
                self.server_socket.listen(5)
                self.server_running = True
                self.stop_event.clear()

                self.file_count_var.set(0)
                self.data_received_var.set(0)

                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.restart_button.config(state=tk.NORMAL)

                Thread(target=self.accept_connections, daemon=True).start()
                self.logger.info(f"|{'=' * 20 } 📡 Server started on {ip}:{port} {'=' * 20 }|")
                self.append_log(f"|{'=' * 20 } 📡 Server started on {ip}:{port} {'=' * 20 }|")
                # Start the mDNS server
                self.zeroconf, self.mdns_info = mdns_connect.start_mdns_listener(self.base_dir, self.append_mdns_log, port)

            except socket.error as e:
                if e.errno == 10048:  # Address already in use
                    self.logger.error(f"⚠️ Port {port} is already in use.")
                    self.append_log(f"⚠️ Port {port} is already in use.")
                    messagebox.showerror("⚠️ Port Error", f"Port {port} is already in use.")
                else:
                    self.logger.error(f"❌ Failed to start server: {e}")
                    self.append_log(f"❌ Failed to start server: {e}")
            except Exception as e:
                self.logger.error(f"❌ An unexpected error occurred: {e}")
                self.append_log(f"❌ An unexpected error occurred: {e}")
        else:
            self.logger.warning(f"⚠️ Server is already running.")
            self.append_log(f"⚠️ Server is already running.")

    def accept_connections(self):
        while not self.stop_event.is_set():
            try:
                client_socket, addr = self.server_socket.accept()
                self.connections.add(client_socket)
                self.connection_count_var.set(len(self.connections))
                self.logger.info(f"{'  ' * 5} 🔗 Accepted connection from {addr}")
                self.append_log(f"{'  ' * 5} 🔗 Accepted connection from {addr}")
                Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
            except Exception as e:
                if not self.stop_event.is_set():
                    self.logger.error(f"❌ Error accepting connections: {e}")
                    self.append_log(f"❌ Error accepting connections: {e}")
                break

    def handle_client(self, client_socket, addr):
        global file_count_var, data_received_var

        def receive_until_delimiter(delimiter):
            data = b''
            while delimiter.encode('utf-8') not in data:
                chunk = client_socket.recv(self.chunk_size_var.get())
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

        def get_file_extension(filename):
            return os.path.splitext(filename)[1].lower()
        
        def get_file_size(file_path):
            return os.path.getsize(file_path) if os.path.exists(file_path) else 0

        try:
            import json
            # Receive header data
            header_data = receive_until_delimiter(self.DELIMITER)
            
            if header_data == b'Discovery_Request':
                return
                
            if not header_data:
                self.logger.error("❌ Header data not received.")
                self.append_log("❌ Header data not received.")
                client_socket.sendall(b'error')  # Send error response
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
                self.logger.error(f"{'❌' * 10} Unable to decode header data.")
                self.append_log(f"{'❌' * 10} Unable to decode header data.")
                client_socket.sendall(b'Unable to decode header data.')  # Send error response
                return

            # Process metadata
            try:
                metadata = json.loads(header_str.split('\n', 1)[0])
                filename = sanitize_filename(metadata["filename"])
                file_size = metadata["file_size"]
            except (json.JSONDecodeError, KeyError) as e:
                self.logger.error(f"{'❌' * 10} Error processing metadata: {e}")
                self.append_log(f"{'❌' * 10} Error processing metadata: {e}")
                client_socket.sendall(b'Error processing metadata.')  # Send error response
                return
            
            # Validate file type
            file_extension = get_file_extension(filename)

            # Extract allowed extensions from the StringVar
            allowed_extensions = {ext.strip().lower() for ext in self.allowed_extensions_var.get().split(",") if ext.strip()}

            # Check if "All" is specified to allow all file types
            if "all" not in allowed_extensions and file_extension not in allowed_extensions:
                self.logger.warning(f"⚠️ Unsupported file type: {file_extension}")
                self.append_log(f"⚠️ Unsupported file type: {file_extension}")
                client_socket.sendall(b'error: Unsupported file type.')
                return

            # Validate file size
            max_file_size_bytes = int(self.max_file_size_var.get()) * 1024 * 1024  # Convert MB to bytes
            if file_size > max_file_size_bytes:
                self.logger.warning(f"⚠️ File size exceeds limit: {format_size(file_size)}")
                self.append_log(f"⚠️ File size exceeds limit: {format_size(file_size)}")
                client_socket.sendall(b'error: File size exceeds limit.')
                return
        
            # Ensure the bucket directory exists
            ensure_base_dir_exists(self.bucket_dir)

            file_path = os.path.join(self.directory_var.get(), sanitize_filename(filename))
            file_path = get_unique_filename(file_path)  # Ensure unique filename
            self.logger.info(f"💾 Saving file to: {file_path}")
            self.append_log(f"💾 Saving file to: {file_path}")

            # Check if the file already exists and get its size
            bytes_received = get_file_size(file_path)
            client_socket.sendall(f"{bytes_received}".encode('utf-8'))  # Send the current size to the client
            try:
                with open(file_path, 'wb') as f:
                    while bytes_received < file_size:
                        chunk = client_socket.recv(min(self.chunk_size_var.get(), file_size - bytes_received))
                        if not chunk:
                            break
                        f.write(chunk)
                        bytes_received += len(chunk)
                        self.data_received_var.set(self.data_received_var.get() + len(chunk))

                if bytes_received == file_size:
                    self.logger.info(f"✅ File received successfully: {filename} ({format_size(file_size)})")
                    self.append_log(f"✅ File received successfully: {filename} ({format_size(file_size)})")
                    self.file_count_var.set(self.file_count_var.get() + 1)
                    addr_str = f"{addr[0]}:{addr[1]}"
                    self.log_file_to_db(filename, format_size(file_size), file_path,addr_str)
                    client_socket.sendall(b'ok\n')  # Send success response
                else:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    self.logger.warning(f"⚠️ File transfer incomplete: {filename}. Expected {format_size(file_size)}, received {format_size(bytes_received)}")
                    self.append_log(f"⚠️ File transfer incomplete: {filename}. Expected {format_size(file_size)}, received {format_size(bytes_received)}")
                    client_socket.sendall(b'File transfer incomplete.\n')
            except Exception as e:
                if os.path.exists(file_path):
                    os.remove(file_path)
                self.logger.error(f"{'⚠️' * 5} Error during file transfer: {str(e)}")
                self.append_log(f"{'⚠️' * 5} Error during file transfer: {str(e)}")
                client_socket.sendall(b'Error during file transfer.\n')

        except Exception as e:
            self.logger.error(f"{'❗' * 5} Error handling client: {str(e)}")
            self.append_log(f"{'❗' * 5} Error handling client: {str(e)}")
            client_socket.sendall(b'Error handling client.')
        finally:
            client_socket.close()
            self.connections.remove(client_socket)
            self.logger.info(f"✅ Connection with {addr} is closed!")
            self.append_log(f"✅ Connection with {addr} is closed!")
            self.connection_count_var.set(len(self.connections))

    def stop_server(self):
        if not self.server_running:
            messagebox.showwarning("⚠️ Server not running", "The server is not currently running.")
            return
        # Stop the mDNS server
        mdns_connect.stop_mdns_listener(self.zeroconf, self.mdns_info)
        self.server_running = False
        self.stop_event.set()

        for conn in self.connections:
            conn.close()

        self.connections.clear()
        self.connection_count_var.set(0)

        self.stop_button.config(state=tk.DISABLED)
        self.start_button.config(state=tk.NORMAL)
        self.restart_button.config(state=tk.DISABLED)

        self.root.after(500, self.check_server_stopped)

    def check_server_stopped(self):
        try:
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            self.logger.info("🛑 Server stopped.")
            self.append_log("🛑  Server stopped.")
            self.log_session_summary()
        except Exception as e:
            self.logger.error(f"❌ Error stopping the server: {e}")
            self.append_log(f"❌ Error stopping the server: {e}")

    def restart_server(self):
        self.append_log("🔄 Restarting the server...")
        self.stop_server()
        self.root.after(1000, self.start_server)

    def clear_logs(self):
        self.log_text.delete('1.0', tk.END)
        self.mdns_log_text.delete('1.0', tk.END)

    def log_session_summary(self):
        session_table = (
            "✨📊  Session Summary  📊✨\n"
            f"{'=' * 46}\n"
            "| Parameter               | Value         |\n"
            f"{'=' * 46}\n"
            f"| 📁 Files Processed     | {str(self.file_count_var.get()).ljust(14)}|\n"
            f"| 🗂 Data Received        | {format_size(self.data_received_var.get()).ljust(14)}|\n"
            f"| 🔄 Chunk Size          | {format_size(self.chunk_size_var.get()).ljust(14)}|\n"
            f"{'=' * 46}\n"
            f"🔚 {'=' * 42} 🔚\n"
        )

        self.logger.info(session_table)
        self.append_log(session_table)

    def apply_settings(self):
        new_ip = self.server_ip_var.get().strip()
        new_port = self.server_port_var.get()
        new_chunk_size = self.chunk_size_var.get()
        new_dir = self.directory_var.get().strip()
        new_extensions = self.allowed_extensions_var.get().strip()
        new_max_size = self.max_file_size_var.get()

        # Validate IP address
        if not is_valid_ip(new_ip):
            messagebox.showerror("Invalid IP", "The provided IP address is invalid.")
            return

        # Validate port
        if not is_valid_port(new_port):
            messagebox.showerror("Invalid Port", "The provided port number is invalid. It must be between 0 and 65535.")
            return

        # Validate chunk size
        if not is_valid_chunk_size(new_chunk_size):
            messagebox.showerror("Invalid Chunk Size", "The chunk size must be a positive integer.")
            return

        # Validate directory
        if not new_dir:
            messagebox.showerror("Invalid Directory", "The directory field cannot be empty.")
            return

        # Validate allowed extensions
        try:
            allowed_extensions = {ext.strip().lower() for ext in new_extensions.split(",") if ext.strip()}
            if not allowed_extensions:
                raise ValueError("No valid extensions provided.")
        except Exception as e:
            messagebox.showerror("Invalid Extensions", f"Error processing extensions: {e}")
            return

        # Validate max file size
        try:
            max_file_size_bytes = int(new_max_size) * 1024 * 1024  # Convert MB to bytes
            if max_file_size_bytes <= 0:
                raise ValueError("Max file size must be greater than 0.")
        except Exception as e:
            messagebox.showerror("Invalid Max Size", f"Error processing max file size: {e}")
            return

        # Ensure the base directory exists
        ensure_base_dir_exists(new_dir)

        # Notify success
        messagebox.showinfo("Settings", "Settings updated successfully.")

        # Log settings summary with processed values
        self.log_settings_summary(
            new_ip, 
            new_port, 
            new_chunk_size, 
            new_dir, 
            new_extensions, 
            new_max_size  # Convert back to MB for logging
        )

        # Restart the server if running
        if self.server_running:
            self.restart_server()

    def log_settings_summary(self, ip, port, chunk_size, _dir, extensions, max_size):
        try:
            # Split and clean extensions
            cleaned_extensions = [ext.strip().lower() for ext in extensions.split(",") if ext.strip()]
            extensions_list = ", ".join(cleaned_extensions)
        except Exception as e:
            extensions_list = "Invalid extensions"
            self.logger.error(f"Error processing extensions for logging: {e}")
        
        settings_table = (
            "⚙️  Settings applied:\n"
            "----------------------------------------------\n"
            "| Parameter          | Value                |\n"
            "----------------------------------------------\n"
            f"| Server IP          | {str(ip).ljust(20)} |\n"
            f"| Port               | {str(port).ljust(20)} |\n"
            f"| Chunk Size         | {format_size(chunk_size).ljust(20)} |\n"
            f"| Directory          | {_dir.ljust(20)} |\n"
            f"| Allowed Extensions | {extensions_list.ljust(20)} |\n"
            f"| Max File Size      | {str(max_size).ljust(20)} MB |\n"
            "----------------------------------------------\n"
        )

        self.logger.info(settings_table)
        self.append_log(settings_table)

# Run the server
if __name__ == "__main__":
    server = TransferXServer()
    updater.check_updates_async()
    tk.mainloop()