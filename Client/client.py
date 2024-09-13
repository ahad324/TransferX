import socket, re, time, zipfile, json, sys, os
from tkinter import ttk,Button, filedialog, messagebox, Label, Entry, StringVar, ttk, Toplevel, font, Listbox
from threading import Thread
from tkinterdnd2 import DND_FILES, TkinterDnD
from pathlib import Path
import udp_connect

# Determine the user's Downloads folder path
def get_downloads_folder():
    if sys.platform == "win32":
        # Windows
        return Path(os.environ['USERPROFILE']) / 'Downloads'
    elif sys.platform == "darwin":
        # macOS
        return Path.home() / 'Downloads'
    elif sys.platform == "linux":
        # Linux
        return Path.home() / 'Downloads'
    else:
        # Other platforms
        return Path.home()

# Determine the base directory for file operations
if getattr(sys, 'frozen', False):
    CURRENT_DIR = Path(sys._MEIPASS)
    BASE_DIR = get_downloads_folder() / 'TransferX'
else:
    CURRENT_DIR = Path(__file__).parent
    BASE_DIR = CURRENT_DIR

def ensure_base_dir_exists():
    if not BASE_DIR.exists():
        BASE_DIR.mkdir(parents=True, exist_ok=True)

# Create the base directory if it doesn't exist
ensure_base_dir_exists()

# Constants
DEFAULT_SERVER_IP = '192.168.1.102'
DEFAULT_SERVER_PORT = 5000
DEFAULT_CHUNK_SIZE = 8192
DELIMITER = "---END-HEADER---"
FONT = 'Segoe UI'
PASSWORD = "ahad"
TIMEOUT = 5

# Define colors
WHITE_COLOR = 'white'
BLACK_COLOR = 'black'
BG_COLOR_LIGHT = '#F0F2F5'
BG_COLOR_DARK = '#343A40'
BUTTON_COLOR_LIGHT = '#007BFF'
BUTTON_COLOR_DARK = '#0056b3'
ENTRY_BG_COLOR = WHITE_COLOR
ENTRY_FG_COLOR = '#212529'
PROGRESSBAR_COLOR = '#28A745'
BUTTON_HOVER_COLOR = '#0056b3'
ERROR_COLOR = "red"
SUCCESS_COLOR = "green"

# To set the icon on every window
def set_window_icon(window):
    current_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    logo_path = os.path.join(current_dir, 'Logo', 'logo.ico')
    window.iconbitmap(logo_path)

# Initialize the Tkinter root window
root = TkinterDnD.Tk()
root.title("TransferX")
root.geometry("800x600")
root.minsize(300, 300)
set_window_icon(root)
root.option_add("*Font", font.Font(family=FONT)) # Apply the font globally

# Tkinter Variables
server_ip_var = StringVar(value=DEFAULT_SERVER_IP)
server_port_var = StringVar(value=DEFAULT_SERVER_PORT)
chunk_size_var = StringVar(value=DEFAULT_CHUNK_SIZE)
roll_no_var = StringVar()

# Styling
style = ttk.Style()
style.configure('TButton', font=(FONT, 12), padding=10, relief='flat', background=BUTTON_COLOR_LIGHT)
style.configure('TLabel', font=(FONT, 16), padding=10)
style.configure('TEntry', font=(FONT, 18), padding=10, relief='raised')
style.configure('TProgressbar', thickness=30, troughcolor='#D3D3D3')

def set_light_theme():
    root.tk_setPalette(background=BG_COLOR_LIGHT, foreground='#000000')
    style.configure('TButton', background=BUTTON_COLOR_LIGHT, foreground=WHITE_COLOR)
    style.configure('TLabel', background=BG_COLOR_LIGHT, foreground='#000000')
    style.configure('TEntry', background=ENTRY_BG_COLOR, foreground=ENTRY_FG_COLOR)
    style.configure('TProgressbar', background=PROGRESSBAR_COLOR, troughcolor='#D3D3D3')

def set_dark_theme():
    root.tk_setPalette(background=BG_COLOR_DARK, foreground=WHITE_COLOR)
    style.configure('TButton', background=BUTTON_COLOR_DARK, foreground=WHITE_COLOR)
    style.configure('TLabel', background=BG_COLOR_DARK, foreground=WHITE_COLOR)
    style.configure('TEntry', background=ENTRY_BG_COLOR, foreground=ENTRY_FG_COLOR)
    style.configure('TProgressbar', background=BUTTON_COLOR_DARK, troughcolor='#3C3C3C')

def toggle_theme():
    global theme
    if theme == 'light':
        set_dark_theme()
        theme = 'dark'
    else:
        set_light_theme()
        theme = 'light'

theme = 'light'
set_light_theme()

def center_window(window, width, height):
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    position_top = int(screen_height / 2 - height / 2)
    position_right = int(screen_width / 2 - width / 2)
    window.geometry(f'{width}x{height}+{position_right}+{position_top}')

# Center the main application window
root.after(100, lambda: center_window(root, 800, 600))

# Theme Toggle Button
theme_button = Button(root, text="🌙", command=toggle_theme, font=(FONT, 12), bg=BUTTON_COLOR_LIGHT, fg=WHITE_COLOR, borderwidth=0, padx=10, pady=5)
theme_button.place(relx=1, rely=0, anchor='ne')
theme_button.bind("<Enter>", lambda e: theme_button.config(bg=BUTTON_HOVER_COLOR))
theme_button.bind("<Leave>", lambda e: theme_button.config(bg=BUTTON_COLOR_LIGHT))

def create_loading_screen():
    loading_dialog = Toplevel(root)
    loading_dialog.title("Connecting")
    loading_dialog.geometry("300x150")
    set_window_icon(loading_dialog)
    loading_dialog.transient(root)
    loading_dialog.grab_set()

    Label(loading_dialog, text="Finding server, please wait...", font=(FONT, 16)).pack(pady=30)
    progress = ttk.Progressbar(loading_dialog, orient="horizontal", mode="indeterminate", length=250)
    progress.pack(pady=10)
    progress.start()

    loading_dialog.protocol("WM_DELETE_WINDOW", lambda: loading_dialog.destroy() if messagebox.askokcancel("Quit", "Do you want to quit?") else None)
    center_window(loading_dialog, 300, 150)
    
    return loading_dialog

# Auto connect to server Function
def auto_connect():
    loading_dialog = create_loading_screen()

    def on_discovery_complete(result):
        loading_dialog.destroy()  # Close the loading dialog
        if result['status'] == 'error':
            messagebox.showerror("Error", result['message'])
            status_label.config(text="Server Status: Disconnected", fg=ERROR_COLOR)
        elif result['status'] == 'success':
            server_ip_var.set(result['server_ip'])
            messagebox.showinfo("Success", f"Connected to server at {result['server_ip']}")
            status_label.config(text=f"Server Status: Connected to {result['server_ip']}", fg=SUCCESS_COLOR)

    def discovery_with_timeout():
        try:
            result = udp_connect.discover_server_ip(TIMEOUT)
            on_discovery_complete(result)
        except Exception as e:
            on_discovery_complete({"status": "error", "message": f"An unexpected error occurred: {str(e)}"})

    Thread(target=discovery_with_timeout).start()

# Auto-Connect Button
auto_connect_button = Button(
    root,
    text="Connect to Server",
    command=lambda: Thread(target=auto_connect).start(),
    font=(FONT, 12),
    bg=BUTTON_COLOR_LIGHT,
    fg=WHITE_COLOR,
    borderwidth=0,
    padx=10,
    pady=5
)
auto_connect_button.place(relx=0.0, rely=0.0, anchor='nw')
auto_connect_button.bind("<Enter>", lambda e: auto_connect_button.config(bg=BUTTON_HOVER_COLOR))
auto_connect_button.bind("<Leave>", lambda e: auto_connect_button.config(bg=BUTTON_COLOR_LIGHT))

# Roll Number Input
roll_no_label = Label(root, text="Enter your Roll Number:", anchor="center", font=(FONT, 18,"bold"))
roll_no_label.pack(pady=(100, 5))
roll_no_entry = Entry(root, textvariable=roll_no_var, width=30, justify='center',borderwidth=2, relief="solid", highlightthickness=2,font=(FONT, 18), bg=ENTRY_BG_COLOR, fg=ENTRY_FG_COLOR)
roll_no_entry.config(highlightcolor='#007BFF', highlightbackground="#BDBDBD", relief="flat")
roll_no_entry.pack(pady=(5, 10))

# Instructions
instructions = Label(root, text="Drag and drop files here or click 'Select Files' to upload.\nIf multiple files are selected, they will be zipped.", font=(FONT, 18), wraplength=750, justify="center")
instructions.pack(pady=20)

# Function to sanitize the filename to avoid "Directory Traversal attack"
def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def on_drop(event):
    file_paths = root.tk.splitlist(event.data)
    if file_paths:
        # Ensure all dropped items are files
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
            zip_files(file_paths, zip_file_path)
            submit_file(zip_file_path, roll_no)
        else:
            submit_file(file_paths[0], roll_no)

# Register drag-and-drop functionality
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

# Select Files Button
select_button = Button(root, text="Select Files", command=lambda: Thread(target=select_files).start(), font=(FONT, 14), bg=BUTTON_COLOR_LIGHT, fg=WHITE_COLOR, borderwidth=2, padx=15, pady=10)
select_button.pack(pady=30)
select_button.bind("<Enter>", lambda e: select_button.config(bg=BUTTON_HOVER_COLOR))
select_button.bind("<Leave>", lambda e: select_button.config(bg=BUTTON_COLOR_LIGHT))

# Create a frame to hold the status label
status_frame = ttk.Frame(root)
status_frame.pack(side='bottom', anchor='sw', padx=10, pady=10, fill='x')

# Create the status label
status_label = Label(status_frame, text="Server Status: Disconnected", font=(FONT, 14), fg=ERROR_COLOR, anchor='w')
status_label.pack(side='left', fill='x', expand=True)

def create_progress_dialog():
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            dialog.destroy()
            
    dialog = Toplevel(root)
    dialog.title("Uploading")
    dialog.geometry("350x250")
    set_window_icon(dialog)
    dialog.transient(root)
    dialog.grab_set()

    label = Label(dialog, text="Uploading...", font=(FONT, 16))
    label.pack(pady=15)
    progress = ttk.Progressbar(dialog, orient="horizontal", mode="determinate", length=300, style='TProgressbar')
    progress.pack(pady=15)

    progress_label = Label(dialog, text="0%", font=(FONT, 16))
    progress_label.pack(pady=10)
    speed_label = Label(dialog, text="Speed: 0 KB/s", font=(FONT, 14))
    speed_label.pack(pady=5)
    time_label = Label(dialog, text="Time Left: 0m 0s", font=(FONT, 14))
    time_label.pack(pady=5)
    
    center_window(dialog, 350, 250)
    
    # Override the default behavior of the close button
    dialog.protocol("WM_DELETE_WINDOW", on_closing)
    return dialog, progress, progress_label, speed_label, time_label

# Ensure select_files only allows file selection
def select_files():
    file_paths = filedialog.askopenfilenames()
    # Filter out directories from the selected files
    file_paths = [path for path in file_paths if os.path.isfile(path)]
    if file_paths:
        roll_no = roll_no_var.get().strip()
        if not roll_no:
            messagebox.showerror("Error", "Roll Number is required")
            return

        if len(file_paths) > 1:
            zip_file_name = os.path.join(BASE_DIR, f"{sanitize_filename(roll_no)}.zip")
            zip_files(file_paths, zip_file_name)
            submit_file(os.path.join(CURRENT_DIR, zip_file_name), roll_no)
        else:
            submit_file(file_paths[0], roll_no)
def zip_files(file_paths, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))

def update_progress(progress, progress_label, speed_label, time_label, total_sent, file_size, start_time):
    elapsed_time = time.time() - start_time
    speed = total_sent / elapsed_time if elapsed_time > 0 else 0
    estimated_time = (file_size - total_sent) / speed if speed > 0 else 0
    progress['value'] = total_sent
    progress_label['text'] = f"{int((total_sent / file_size) * 100)}%"
    speed_label['text'] = f"Speed: {speed / 1024:.2f} KB/s"
    time_label['text'] = f"Time Left: {estimated_time // 60:.0f}m {estimated_time % 60:.0f}s"
    root.update_idletasks()
    
def submit_file(file_path, roll_no):
    try:
        dialog, progress, progress_label, speed_label, time_label = create_progress_dialog()
        def upload_file():
            try:
                # Create a socket connection
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                
                # Try to connect to the server
                server_ip = server_ip_var.get()
                server_port = int(server_port_var.get())
                
                try:
                    s.connect((server_ip, server_port))
                except (ConnectionRefusedError, OSError) as e:
                    messagebox.showerror("Connection Error", f"Could not connect to the server at {server_ip}:{server_port}. Please make sure the server is running. Error: {e}")
                    dialog.destroy()
                    return

                # Determine the filename based on the file type
                filename = f"{roll_no}.zip" if file_path.endswith('.zip') else f"{roll_no}{os.path.splitext(file_path)[1]}"
                file_size = os.path.getsize(file_path)

                metadata = {
                    "filename": filename,
                    "file_size": file_size,
                }
                metadata_json = json.dumps(metadata)

                header = f"{metadata_json}\n{DELIMITER}\n"
                s.sendall(header.encode())

                progress['maximum'] = file_size
                progress['value'] = 0
                total_sent = 0
                start_time = time.time()

                # Open the file from the correct directory
                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(int(chunk_size_var.get()))
                        if not data:
                            break
                        try:
                            s.sendall(data)
                            total_sent += len(data)
                            update_progress(progress, progress_label, speed_label, time_label, total_sent, file_size, start_time)
                        except ConnectionResetError:
                            messagebox.showerror("Connection Error", "The connection to the server was lost. Please try again.")
                            return

                s.shutdown(socket.SHUT_WR)
                response = s.recv(1024).decode()
                if response == 'ok':
                    messagebox.showinfo("Success", "File uploaded successfully!")
                else:
                    messagebox.showerror("Error", "Failed to upload file.")         
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred during file upload: {str(e)}")
            finally:
                s.close()
                dialog.destroy()

        Thread(target=upload_file).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status_label.config(text="Server Status: Disconnected", fg=ERROR_COLOR)

def create_settings_dialog():
    dialog = Toplevel(root)
    dialog.title("Settings")
    dialog.geometry("400x300")
    set_window_icon(dialog)
    dialog.transient(root)
    dialog.grab_set()

    def apply_settings():
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

            dialog.destroy()
        
        except ValueError as e:
            messagebox.showerror("Error", str(e))

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

    apply_button = Button(dialog, text="Apply", command=apply_settings, font=(FONT, 14), bg=BUTTON_COLOR_LIGHT, fg=WHITE_COLOR, borderwidth=2, padx=10, pady=5)
    apply_button.pack(pady=5)
    apply_button.bind("<Enter>", lambda e: apply_button.config(bg=BUTTON_HOVER_COLOR))
    apply_button.bind("<Leave>", lambda e: apply_button.config(bg=BUTTON_COLOR_LIGHT))

    center_window(dialog, 400, 300)
    return dialog
def ask_for_password():
    def verify_password():
        entered_password = password_var.get()
        if entered_password == PASSWORD:
            password_dialog.destroy()
            create_settings_dialog()
        else:
            messagebox.showerror("Error", "Incorrect password")

    password_dialog = Toplevel(root)
    password_dialog.title("Password Required")
    password_dialog.geometry("300x150")
    set_window_icon(password_dialog)
    password_dialog.transient(root)
    password_dialog.grab_set()

    Label(password_dialog, text="Enter Password:", font=(FONT, 14)).pack(pady=10)
    password_var = StringVar()
    password_entry = Entry(password_dialog, textvariable=password_var, show='*', font=(FONT, 14))
    password_entry.pack(pady=5)
    
    Button(password_dialog, text="Submit", command=verify_password, font=(FONT, 14), bg=BUTTON_COLOR_LIGHT, fg=WHITE_COLOR, borderwidth=2, padx=10, pady=5).pack(pady=10)

    center_window(password_dialog, 300, 150)
    password_entry.focus_set()

def open_settings():
    ask_for_password()

# Settings Button
settings_button = Button(root, text="⚙️ Settings", command=open_settings, font=(FONT, 12), bg=BUTTON_COLOR_LIGHT, fg=WHITE_COLOR, borderwidth=0, padx=10, pady=5)
settings_button.place(relx=1.0, rely=0.0, anchor='ne', x=-120)
settings_button.bind("<Enter>", lambda e: settings_button.config(bg=BUTTON_HOVER_COLOR))
settings_button.bind("<Leave>", lambda e: settings_button.config(bg=BUTTON_COLOR_LIGHT))

def start_app():
    root.mainloop()

if __name__ == "__main__":
    start_app()