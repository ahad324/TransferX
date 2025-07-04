import os
import sys
import time
from pathlib import Path
from utility import get_downloads_folder, ensure_base_dir_exists, set_window_icon, center_window, sanitize_filename, format_size, is_valid_ip, is_valid_port, is_valid_chunk_size
from threading import Thread, Event
from tkinter import Frame, ttk, Button, filedialog, messagebox, Label, Entry, StringVar, Toplevel, font
from tkinterdnd2 import DND_FILES, TkinterDnD

import updater

# Constants
DEFAULT_SERVER_IP = '192.168.1.102'
DEFAULT_SERVER_PORT = 5000
DEFAULT_CHUNK_SIZE = 8192
DELIMITER = "---END-HEADER---"
FONT = 'Poppins'
TIMEOUT = 10
discovery_stop_event = Event()

# Colors
WHITE_COLOR = 'white'
BLACK_COLOR = 'black'
BG_COLOR_LIGHT = '#f9fafb'
BG_COLOR_DARK = '#111827'
BUTTON_COLOR_LIGHT = '#5355d6'
ENTRY_BG_COLOR = WHITE_COLOR
ENTRY_FG_COLOR = '#212529'
PROGRESSBAR_COLOR = '#28A745'
BUTTON_HOVER_COLOR = '#7173fd'
ERROR_COLOR = "red"
SUCCESS_COLOR = "green"
BUTTON_CONFIG = {
    'borderwidth': 0,
    'padx': 10,
    'pady': 5,
    'cursor': "hand2",
    'font': (FONT, 12),
    'bg': BUTTON_COLOR_LIGHT,
    'fg': WHITE_COLOR
}

if getattr(sys, 'frozen', False):
    CURRENT_DIR = Path(sys._MEIPASS)
    BASE_DIR = get_downloads_folder() / 'TransferX'
else:
    CURRENT_DIR = Path(__file__).parent
    BASE_DIR = CURRENT_DIR
    
class ThemeManager:
    def __init__(self, root, developer_label):
        self.root = root
        self.theme = 'light'
        self.developer_label = developer_label

    def set_light_theme(self):
        self.root.tk_setPalette(background=BG_COLOR_LIGHT, foreground=BLACK_COLOR)
        style.configure('TButton', background=BUTTON_COLOR_LIGHT, foreground=WHITE_COLOR)
        style.configure('TLabel', background=BG_COLOR_LIGHT, foreground=BLACK_COLOR)
        style.configure('TEntry', background=ENTRY_BG_COLOR, foreground=ENTRY_FG_COLOR)
        style.configure('TProgressbar', background=PROGRESSBAR_COLOR, troughcolor='#D3D3D3')
        static_status_label.config(fg=BLACK_COLOR)
        self.developer_label.update_theme('light')
        
        # Ensure bluish elements maintain white text
        self.update_bluish_elements(WHITE_COLOR)

    def set_dark_theme(self):
        self.root.tk_setPalette(background=BG_COLOR_DARK, foreground=WHITE_COLOR)
        style.configure('TLabel', background=BG_COLOR_DARK, foreground=WHITE_COLOR)
        style.configure('TEntry', background=ENTRY_BG_COLOR, foreground=ENTRY_FG_COLOR)
        static_status_label.config(fg=WHITE_COLOR)
        roll_no_entry.config(fg=WHITE_COLOR)
        self.developer_label.update_theme('dark')

    def update_bluish_elements(self, text_color):
        # Update all elements with bluish background to have white text
        for widget in [theme_button, auto_connect_button, select_button, settings_button]:
            widget.config(fg=text_color)
            
    def toggle_theme(self):
        if self.theme == 'light':
            self.set_dark_theme()
            self.theme = 'dark'
        else:
            self.set_light_theme()
            self.theme = 'light'
        self.root.update_idletasks()

            
        # Method to update specific frame background
    def update_frame_background(self, frame):
        if self.theme == 'light':
            frame.config(bg=BG_COLOR_LIGHT)
        else:
            frame.config(bg=BG_COLOR_DARK)

# GUI Creation Functions
def create_loading_screen():
    dialog_size = {"width":300,"height":150}
    loading_dialog = Toplevel(root)
    loading_dialog.title("Connecting")
    loading_dialog.geometry(f"{dialog_size['width']}x{dialog_size['height']}")
    loading_dialog.minsize(300,150)
    set_window_icon(loading_dialog)
    loading_dialog.transient(root)
    loading_dialog.grab_set()

    Label(loading_dialog, text="Finding server, please wait...", font=(FONT, 16)).pack(pady=20)
    progress = ttk.Progressbar(loading_dialog, orient="horizontal", mode="indeterminate", length=250)
    progress.pack(pady=10)
    progress.start()

    def on_dialog_close():
            discovery_stop_event.set()  # Signal the discovery process to stop
            loading_dialog.destroy()
            messagebox.showinfo("Discovery Cancelled", "Server discovery has been cancelled.")
            update_connection_status("Disconnected", ERROR_COLOR)

    loading_dialog.protocol("WM_DELETE_WINDOW", on_dialog_close)
    center_window(loading_dialog, dialog_size["width"], dialog_size['height'])
    
    return loading_dialog

def create_progress_dialog():
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            dialog.destroy()
            
    dialog_size = {"width":400,"height":300}
    dialog = Toplevel(root)
    dialog.title("Uploading")
    dialog.geometry(f"{dialog_size['width']}x{dialog_size['height']}")
    dialog.minsize(400,300)
    set_window_icon(dialog)
    dialog.transient(root)
    dialog.grab_set()

    label = Label(dialog, text="Uploading...", font=(FONT, 16))
    label.pack(pady=15)
    progress = ttk.Progressbar(dialog, orient="horizontal", mode="determinate", length=300, style='TProgressbar')
    progress.pack(pady=15)

    progress_label = Label(dialog, text="0%", font=(FONT, 16))
    progress_label.pack(pady=10)
    sent_label = Label(dialog, text="Sent: 0 B/0 B", font=(FONT, 12))
    sent_label.pack(pady=5)
    time_speed_frame = Frame(dialog)
    time_speed_frame.pack(pady=5)
    speed_label = Label(time_speed_frame, text="Speed: 0 KB/s", font=(FONT, 12))
    speed_label.pack(side="left", padx=5)
    time_label = Label(time_speed_frame, text="Time Left: 0m 0s", font=(FONT, 12))
    time_label.pack(side="left", padx=5)
    
    center_window(dialog, dialog_size["width"], dialog_size["height"])

    
    dialog.protocol("WM_DELETE_WINDOW", on_closing)
    return dialog, progress, progress_label, speed_label, time_label, sent_label

def create_zip_progress_dialog(on_cancel):
    def on_closing():
        if messagebox.askokcancel("Cancel Operation", "Are you sure you want to cancel the zipping process?"):
            on_cancel()
            dialog.destroy()

    dialog_size = {"width": 400, "height": 400}
    dialog = Toplevel(root)
    dialog.title("Zipping Files")
    dialog.geometry(f"{dialog_size['width']}x{dialog_size['height']}")
    dialog.minsize(400,400)
    set_window_icon(dialog)
    dialog.transient(root)
    dialog.grab_set()

    # Title and Progress Bar
    Label(dialog, text="Zipping Your Files...", font=(FONT, 16, "bold")).pack(pady=10)
    progress = ttk.Progressbar(dialog, orient="horizontal", mode="determinate", length=350, style='TProgressbar')
    progress.pack(pady=15)

    # Overall Progress
    zip_progress_label = Label(dialog, text="Progress: 0%", font=(FONT, 14, "bold"))
    zip_progress_label.pack(pady=5)
    files_zipped_label = Label(dialog, text="Files Processed: 0/0", font=(FONT, 14))
    files_zipped_label.pack(pady=5)
    
    # Current File Info
    file_info_frame = Frame(dialog)
    file_info_frame.pack(pady=10)
    file_name_label = Label(file_info_frame, text="Currently Processing: N/A", font=(FONT, 11), wraplength=350)
    file_name_label.pack()
    file_size_label = Label(file_info_frame, text="File Size: N/A", font=(FONT, 11))
    file_size_label.pack()

    # Cancel Button
    cancel_button = Button(dialog, text="Stop Zipping", command=on_closing, **BUTTON_CONFIG)
    cancel_button.pack(pady=20)
    cancel_button.bind("<Enter>", lambda e: cancel_button.config(bg=BUTTON_HOVER_COLOR))
    cancel_button.bind("<Leave>", lambda e: cancel_button.config(bg=BUTTON_COLOR_LIGHT))


    center_window(dialog, dialog_size["width"], dialog_size["height"])

    dialog.protocol("WM_DELETE_WINDOW", on_closing)
    return dialog, progress, file_name_label, file_size_label, files_zipped_label, zip_progress_label

def create_settings_dialog():
    dialog_size = {"width":400,"height":400}
    dialog = Toplevel(root)
    dialog.title("Settings")
    dialog.geometry(f"{dialog_size['width']}x{dialog_size['height']}")
    dialog.minsize(400,400)
    dialog.transient(root)
    set_window_icon(dialog)
    dialog.grab_set()

    def update_settings():
        try:
            new_ip = ip_entry.get()
            new_port = int(port_entry.get())
            new_chunk_size = int(chunk_size_entry.get())

            if not is_valid_ip(new_ip):
                raise ValueError("Invalid IP address")
            if not is_valid_port(new_port):
                raise ValueError("Port number must be between 0 and 65535")
            if not is_valid_chunk_size(new_chunk_size):
                raise ValueError("Chunk size must be a positive integer")

            server_ip_var.set(new_ip)
            server_port_var.set(new_port)
            chunk_size_var.set(new_chunk_size)
            messagebox.showinfo("Success", "Settings updated successfully!")
            
            def check_connection(new_ip):
                loading_dialog = create_loading_screen()

                def async_discovery():
                    result = start_server_discovery(new_ip)
                    if result is None:
                        if loading_dialog.winfo_exists():
                            loading_dialog.destroy()
                    else:
                        on_discovery_complete(result, loading_dialog)
                Thread(target=async_discovery).start()

            check_connection(new_ip)
            dialog.destroy()
        
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    Label(dialog, text="Server IP:", font=(FONT, 14)).pack(pady=5)
    ip_entry = Entry(dialog, font=(FONT, 14))
    ip_entry.insert(0, server_ip_var.get())
    ip_entry.pack(pady=5)

    Label(dialog, text="Server Port:", font=(FONT, 14)).pack(pady=5)
    port_entry = Entry(dialog, font=(FONT, 14))
    port_entry.insert(0, server_port_var.get())
    port_entry.pack(pady=5)

    Label(dialog, text="Chunk Size:", font=(FONT, 14)).pack(pady=5)
    chunk_size_entry = Entry(dialog, font=(FONT, 14))
    chunk_size_entry.insert(0, chunk_size_var.get())
    chunk_size_entry.pack(pady=5)

    update_settings_button = Button(dialog, text="Update settings", command=update_settings, **BUTTON_CONFIG)
    update_settings_button.pack(pady=20)
    update_settings_button.bind("<Enter>", lambda e: update_settings_button.config(bg=BUTTON_HOVER_COLOR))
    update_settings_button.bind("<Leave>", lambda e: update_settings_button.config(bg=BUTTON_COLOR_LIGHT))

    center_window(dialog, dialog_size["width"], dialog_size["height"])
    return dialog

# File Operations
def zip_files(file_paths, zip_file_path, on_complete):
    def zip_thread():
        import zipfile
        def on_cancel():
            nonlocal cancel_requested
            cancel_requested = True
            dialog.destroy()

        cancel_requested = False
        dialog, progress, file_name_label, file_size_label, files_zipped_label, zip_progress_label = create_zip_progress_dialog(on_cancel)
        ensure_base_dir_exists(BASE_DIR)
        
        total_files = len(file_paths)
        total_size = sum(os.path.getsize(file) for file in file_paths)
        zipped_files = 0
        total_zipped_size = 0
        progress['maximum'] = 100
        chunk_size = int(chunk_size_var.get())

        try:
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zipf:
                for i, file in enumerate(file_paths):
                    if cancel_requested:
                        break
                    file_name = os.path.basename(file)
                    file_size = os.path.getsize(file)
                    file_name_label.config(text=f"Currently Processing: {file_name}")
                    file_size_label.config(text=f"File Size: {format_size(file_size)}")

                    with open(file, 'rb') as f:
                        zinfo = zipfile.ZipInfo.from_file(file, file_name)
                        zinfo.compress_type = zipfile.ZIP_DEFLATED
                        with zipf.open(zinfo, mode='w') as dest:
                            file_zipped_size = 0
                            while True:
                                if cancel_requested:
                                    break
                                chunk = f.read(chunk_size)
                                if not chunk:
                                    break
                                dest.write(chunk)
                                file_zipped_size += len(chunk)
                                total_zipped_size += len(chunk)
                                
                                overall_progress = (total_zipped_size / total_size) * 100
                                progress['value'] = overall_progress
                                zip_progress_label.config(text=f"Progress: {overall_progress:.1f}%")
                                root.update_idletasks()

                    zipped_files += 1
                    files_zipped_label.config(text=f"Files Processed: {zipped_files}/{total_files}")
                    root.update_idletasks()

        except Exception as e:
            if cancel_requested:
                os.remove(zip_file_path)
                messagebox.showinfo("Cancelled", "The zipping process was cancelled.")
            else:
                on_cancel()
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
            return

        if not cancel_requested:
            dialog.destroy()
            on_complete(zip_file_path)

    Thread(target=zip_thread, daemon=True).start()

def submit_file(file_path, roll_no):
    def start_upload():
        cancel_upload = False
        is_temp_zip = file_path.startswith(str(BASE_DIR)) and file_path.endswith('.zip')  # Track if this is our temporary zip

        dialog, progress, progress_label, speed_label, time_label, sent_label = create_progress_dialog()
        def on_cancel():
            nonlocal cancel_upload
            if messagebox.askyesno("Confirm Cancellation", "Are you sure you want to cancel the upload?"):
                cancel_upload = True
                dialog.destroy()

        dialog.protocol("WM_DELETE_WINDOW", on_cancel)

        def upload_file():
            nonlocal cancel_upload
            try:
                import socket
                import json
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(30)  # Set a 30-second timeout
                
                server_ip = server_ip_var.get()
                server_port = int(server_port_var.get())
                
                try:
                    s.connect((server_ip, server_port))
                except (ConnectionRefusedError, OSError) as e:
                    raise Exception(f"Could not connect to the server at {server_ip}:{server_port}. Error: {e}")

                filename = f"{roll_no}.zip" if file_path.endswith('.zip') else f"{roll_no}{os.path.splitext(file_path)[1]}"
                file_size = os.path.getsize(file_path)

                metadata = {
                    "filename": filename,
                    "file_size": file_size,
                }
                metadata_json = json.dumps(metadata)

                header = f"{metadata_json}\n{DELIMITER}\n"
                s.sendall(header.encode('utf-8'))

                # Receive the current size of the file on the server
                bytes_sent = int(s.recv(1024).decode('utf-8').strip())
                
                progress['maximum'] = file_size
                progress['value'] = bytes_sent
                total_sent = 0
                start_time = time.time()

                chunk_size = int(chunk_size_var.get())
                with open(file_path, 'rb') as f:
                    while True:
                        if cancel_upload:
                            raise Exception("Upload canceled by user")
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        bytes_sent = 0
                        while bytes_sent < len(chunk):
                            s.sendall(chunk[bytes_sent:])
                            bytes_sent += len(chunk)
                        total_sent += bytes_sent
                        update_progress(progress, progress_label, speed_label, time_label, sent_label, total_sent, file_size, start_time)
                        if not dialog.winfo_exists():
                            raise Exception("Upload canceled by user")

                s.shutdown(socket.SHUT_WR)
                
                if total_sent != file_size:
                    raise Exception(f"File size mismatch. Sent {format_size(total_sent)}, expected {format_size(file_size)}.")

                s.settimeout(TIMEOUT)  # Set a 10-second timeout for receiving the response
                response = s.recv(1024).decode('utf-8').strip()
                if response == 'ok':
                    if not cancel_upload:
                        dialog.after(0, dialog.destroy)
                        messagebox.showinfo("Success", "File uploaded successfully!")
                        if is_temp_zip and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                messagebox.showerror("Error", "Error removing temporary zip: {e}")
                    return True  # Indicate successful upload
                else:
                    raise Exception(f"Server response: {response}")

            except Exception as e:
                if not cancel_upload:
                    error_msg = f"Upload failed. Error: {str(e)}"
                    dialog.after(0, lambda: messagebox.showerror("Error", error_msg) if dialog.winfo_exists() else None)
            finally:
                s.close()

            if dialog.winfo_exists():
                dialog.after(0, dialog.destroy)
            return False  # Indicate failed upload

        Thread(target=upload_file).start()

    show_file_metadata([file_path], start_upload)

# Server Discovery and Connection
def start_server_discovery(ip=None):
    from mdns_connect import discover_server
    global discovery_stop_event
    discovery_stop_event.clear()  # Reset the event
    try:
        if ip is None:
            result = discover_server(timeout=TIMEOUT, stop_event=discovery_stop_event)
        else:
            result = discover_server(ip, TIMEOUT, stop_event=discovery_stop_event)
        
        return result
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

def on_discovery_complete(result, loading_dialog):
    if loading_dialog.winfo_exists():
        loading_dialog.destroy()
    if discovery_stop_event.is_set():
        # If the discovery was canceled, do not show any message
        return
    if result['status'] == 'error':
        messagebox.showerror("Error", result['message'])
        update_connection_status("Disconnected", ERROR_COLOR)
    elif result['status'] == 'success':
        server_ip_var.set(result['server_ip'])
        server_port_var.set(result['server_port'])
        messagebox.showinfo("Success", f"Connected to server at {result['server_ip']}:{result['server_port']}")
        update_connection_status(f"Connected to {result['server_ip']}:{result['server_port']}", SUCCESS_COLOR)

def auto_connect():
    loading_dialog = create_loading_screen()

    def async_discovery():
        result = start_server_discovery()
        if result is None:
            if loading_dialog.winfo_exists():
                loading_dialog.destroy()
        else:
            on_discovery_complete(result, loading_dialog)

    Thread(target=async_discovery).start()

# UI Event Handlers
def on_drop(event):
    file_paths = root.tk.splitlist(event.data)
    if file_paths:
        file_paths = [path for path in file_paths if os.path.isfile(path)]
        if not file_paths:
            messagebox.showerror("Error", "Only files can be uploaded. Please do not drop folders.")
            return
        
        roll_no = roll_no_var.get().strip()
        if not roll_no:
            messagebox.showerror("Error", "Roll Number is required")
            return

        if len(file_paths) > 1:
            zip_file_name = f"{sanitize_filename(roll_no)}.zip"
            zip_file_path = os.path.join(BASE_DIR, zip_file_name)
            zip_files(file_paths, zip_file_path, lambda path: submit_file(path, roll_no))
        else:
            submit_file(file_paths[0], roll_no)

def select_files():
    file_paths = filedialog.askopenfilenames()
    file_paths = [path for path in file_paths if os.path.isfile(path)]
    if file_paths:
        roll_no = roll_no_var.get().strip()
        if not roll_no:
            messagebox.showerror("Error", "Roll Number is required")
            return

        if len(file_paths) > 1:
            zip_file_name = f"{sanitize_filename(roll_no)}.zip"
            zip_file_path = os.path.join(BASE_DIR, zip_file_name)
            zip_files(file_paths, zip_file_path, lambda path: submit_file(path, roll_no))
        else:
            submit_file(file_paths[0], roll_no)

def show_file_metadata(file_paths, callback_on_upload):
    if not file_paths:
        return

    if len(file_paths) > 1:
        zip_file_name = f"{sanitize_filename(roll_no_var.get())}.zip"
        zip_file_path = os.path.join(BASE_DIR, zip_file_name)
        zip_files(file_paths, zip_file_path)
        file_paths = [zip_file_path]

    metadata = []
    for file in file_paths:
        _, file_extension = os.path.splitext(file)
        name = f"{roll_no_var.get()}{file_extension}"
        size = os.path.getsize(file)
        formatted_size = format_size(size)
        metadata.append(f"Name: {name}\nSize: {formatted_size}\n")

    metadata_text = "\n\n".join(metadata)

    def on_upload():
        dialog.destroy()
        callback_on_upload()

    def on_cancel():
        dialog.destroy()
        
    dialog_size = {"width":400,"height":250}
    dialog = Toplevel(root)
    dialog.title("File Metadata")
    dialog.geometry(f"{dialog_size['width']}x{dialog_size['height']}")
    dialog.minsize(dialog_size['width'], dialog_size['height'])
    set_window_icon(dialog)
    dialog.transient(root)
    dialog.grab_set()

    Label(dialog, text="The following file will be uploaded:", font=(FONT, 16)).pack(pady=10)
    Label(dialog, text=metadata_text, font=(FONT, 14,"bold"), justify='left').pack(pady=0)

    button_frame = Frame(dialog, bg=BG_COLOR_LIGHT)
    button_frame.pack(pady=0)
    theme_manager.update_frame_background(button_frame)

    upload_button = Button(button_frame, text="Upload file", command=on_upload, **BUTTON_CONFIG)
    upload_button.pack(side='left', padx=10)
    upload_button.bind("<Enter>", lambda e: upload_button.config(bg=BUTTON_HOVER_COLOR))
    upload_button.bind("<Leave>", lambda e: upload_button.config(bg=BUTTON_COLOR_LIGHT))

    cancel_button = Button(button_frame, text="Cancel", command=on_cancel, **BUTTON_CONFIG)
    cancel_button.pack(side='right', padx=10)
    cancel_button.bind("<Enter>", lambda e: cancel_button.config(bg=BUTTON_HOVER_COLOR))
    cancel_button.bind("<Leave>", lambda e: cancel_button.config(bg=BUTTON_COLOR_LIGHT))


    center_window(dialog, dialog_size["width"], dialog_size["height"])

def update_progress(progress, progress_label, speed_label, time_label, sent_label, total_sent, file_size, start_time):
    elapsed_time = time.time() - start_time
    speed = total_sent / elapsed_time if elapsed_time > 0 else 0
    estimated_time = (file_size - total_sent) / speed if speed > 0 else 0
    progress['value'] = total_sent
    progress_label['text'] = f"{int((total_sent / file_size) * 100)}%"
    speed_label['text'] = f"Speed: {speed / 1024:.2f} KB/s"
    time_label['text'] = f"Time Left: {estimated_time // 60:.0f}m {estimated_time % 60:.0f}s"
    sent_label['text'] = f"Sent: {format_size(total_sent)} / {format_size(file_size)}"
    root.update_idletasks()

def update_connection_status(message, color):
    dynamic_status_label.config(text=message, fg=color)

def open_settings():
    create_settings_dialog()

# Main Application Setup

ensure_base_dir_exists(BASE_DIR)

root_window_minsize = (800, 600)
root = TkinterDnD.Tk()
root.title("TransferX")
root.state('zoomed')
root.minsize(root_window_minsize[0],root_window_minsize[1])
set_window_icon(root)
root.option_add("*Font", font.Font(family=FONT))

# Bottom Frame
bottom_frame = Frame(root)
bottom_frame.pack(side='bottom', fill='x', padx=5, pady=5)

# Status Labels
status_left_frame = Frame(bottom_frame)
status_left_frame.pack(side='left')

static_status_label = Label(status_left_frame, text="Connection Status:", font=(FONT, 16, "bold"), fg=BLACK_COLOR, anchor='w')
static_status_label.pack(side='left')
dynamic_status_label = Label(status_left_frame, text="Disconnected", font=(FONT, 16, "bold"), fg=ERROR_COLOR, anchor='w')
dynamic_status_label.pack(side='left')


from developer_label import create_developer_label
# Developer Label
developer_label = create_developer_label(
    bottom_frame,
    FONT,
    light_theme={'bg': BG_COLOR_LIGHT, 'fg': BLACK_COLOR},
    dark_theme={'bg': BG_COLOR_DARK, 'fg': WHITE_COLOR}
)

# Theme Manager
theme_manager = ThemeManager(root, developer_label)

# Server Configuration
server_ip_var = StringVar(value=DEFAULT_SERVER_IP)
server_port_var = StringVar(value=DEFAULT_SERVER_PORT)
chunk_size_var = StringVar(value=DEFAULT_CHUNK_SIZE)
roll_no_var = StringVar()

# Style Configuration
style = ttk.Style()
style.configure('TButton', font=(FONT, 12), padding=10, relief='flat', background=BUTTON_COLOR_LIGHT)
style.configure('TLabel', font=(FONT, 16), padding=10)
style.configure('TEntry', font=(FONT, 18), padding=10, relief='raised')
style.configure('TProgressbar', thickness=30, troughcolor='#D3D3D3')

# UI Elements
theme_button = Button(root, text="🌙", command=theme_manager.toggle_theme, **BUTTON_CONFIG)
theme_button.place(relx=1, rely=0, anchor='ne')
theme_button.bind("<Enter>", lambda e: theme_button.config(bg=BUTTON_HOVER_COLOR))
theme_button.bind("<Leave>", lambda e: theme_button.config(bg=BUTTON_COLOR_LIGHT))

auto_connect_button = Button(
    root,
    text="Connect to Server",
    command=lambda: Thread(target=auto_connect).start(),
    **BUTTON_CONFIG
)
auto_connect_button.place(relx=0.0, rely=0.0, anchor='nw')
auto_connect_button.bind("<Enter>", lambda e: auto_connect_button.config(bg=BUTTON_HOVER_COLOR))
auto_connect_button.bind("<Leave>", lambda e: auto_connect_button.config(bg=BUTTON_COLOR_LIGHT))

roll_no_label = Label(root, text="Enter your Roll Number:", anchor="center", font=(FONT, 18, "bold"))
roll_no_label.pack(pady=(100, 5))
roll_no_entry = Entry(root, textvariable=roll_no_var, width=30, justify='center', borderwidth=2, relief="solid", highlightthickness=2, font=(FONT, 18), bg=ENTRY_BG_COLOR, fg=ENTRY_FG_COLOR)
roll_no_entry.config(highlightcolor='#007BFF', highlightbackground="#BDBDBD", relief="flat")
roll_no_entry.pack(pady=(5, 10))

instructions = Label(root, text="Drag & drop files here or click 'Select Files' to upload.\nIf multiple files are selected, they will be zipped.", font=(FONT, 16), wraplength=750, justify="center")
instructions.pack(pady=20)

# Drag and Drop Configuration
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

select_button = Button(root, text="Select Files", command=lambda: Thread(target=select_files).start(),width=15, bg=BUTTON_COLOR_LIGHT, fg=WHITE_COLOR, cursor="hand2", borderwidth=0, font=(FONT,14))
select_button.pack(pady=20)
select_button.bind("<Enter>", lambda e: select_button.config(bg=BUTTON_HOVER_COLOR))
select_button.bind("<Leave>", lambda e: select_button.config(bg=BUTTON_COLOR_LIGHT))

# version & app update details label
version_label = Label(root, text=f"version {updater.AppVersion}", font=(FONT, 12, "italic"), fg=BLACK_COLOR)
version_label.pack(pady=(5, 10))
updater.set_version_label(version_label)

# Official Website Section
website_frame = Frame(root)
website_frame.pack(pady=5)

# Official Website Label
official_website_label = Label(website_frame, text="Official Website:", font=(FONT, 12, "bold"), fg=BLACK_COLOR)
official_website_label.pack(side="left")

# Website Link
website_link = Label(website_frame, text="transferx.netlify.app", font=(FONT, 12, "italic", "underline"), cursor="hand2")
website_link.pack(side="right")

# Function to open the website
def open_website(event):
    import webbrowser
    webbrowser.open("https://transferx.netlify.app/")

# Bind the click event to the website link
website_link.bind("<Button-1>", open_website)

settings_button = Button(root, text="⚙️ Settings", command=open_settings, **BUTTON_CONFIG)
settings_button.place(relx=1.0, rely=0.0, anchor='ne', x=-120)
settings_button.bind("<Enter>", lambda e: settings_button.config(bg=BUTTON_HOVER_COLOR))
settings_button.bind("<Leave>", lambda e: settings_button.config(bg=BUTTON_COLOR_LIGHT))

def start_app():
    theme_manager.set_light_theme()
    root.mainloop()

# Main Execution
if __name__ == '__main__':
    updater.check_updates_async()
    start_app()