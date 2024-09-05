import socket
import os
import json
import zipfile
import time
from tkinter import Button, filedialog, messagebox, Label, Entry, StringVar, ttk, Toplevel
from threading import Thread
from tkinterdnd2 import DND_FILES, TkinterDnD

# Constants
DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 5000
DEFAULT_CHUNK_SIZE = 4096
DELIMITER = "---END-HEADER---"
FONT = 'Segoe UI'

# Define colors
BUTTON_COLOR_LIGHT = '#007BFF'
BUTTON_COLOR_DARK = '#0056b3'
BG_COLOR_LIGHT = '#F0F2F5'
BG_COLOR_DARK = '#343A40'
ENTRY_BG_COLOR = '#FFFFFF'
ENTRY_FG_COLOR = '#212529'
PROGRESSBAR_COLOR = '#28A745'
BUTTON_HOVER_COLOR = '#0056b3'

# Initialize the root window
root = TkinterDnD.Tk()
root.title("TransferX")

# Tkinter Variables
server_ip_var = StringVar(value=DEFAULT_SERVER_IP)
server_port_var = StringVar(value=DEFAULT_SERVER_PORT)
chunk_size_var = StringVar(value=DEFAULT_CHUNK_SIZE)
roll_no_var = StringVar()

# Set the initial window size
root.geometry("800x600")
root.minsize(800, 600)

# Styling
style = ttk.Style()
style.configure('TButton', font=(FONT, 12), padding=10, relief='flat', background=BUTTON_COLOR_LIGHT)
style.configure('TLabel', font=(FONT, 16), padding=10)
style.configure('TEntry', font=(FONT, 18), padding=10, relief='flat')
style.configure('TProgressbar', thickness=30, troughcolor='#D3D3D3')

def set_light_theme():
    root.tk_setPalette(background=BG_COLOR_LIGHT, foreground='#000000')
    style.configure('TButton', background=BUTTON_COLOR_LIGHT, foreground='#FFFFFF')
    style.configure('TLabel', background=BG_COLOR_LIGHT, foreground='#000000')
    style.configure('TEntry', background=ENTRY_BG_COLOR, foreground=ENTRY_FG_COLOR)
    style.configure('TProgressbar', background=PROGRESSBAR_COLOR, troughcolor='#D3D3D3')

def set_dark_theme():
    root.tk_setPalette(background=BG_COLOR_DARK, foreground='#FFFFFF')
    style.configure('TButton', background=BUTTON_COLOR_DARK, foreground='#FFFFFF')
    style.configure('TLabel', background=BG_COLOR_DARK, foreground='#FFFFFF')
    style.configure('TEntry', background='#3C3C3C', foreground=ENTRY_FG_COLOR)
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
theme_button = Button(root, text="🌙", command=toggle_theme, font=(FONT, 12), bg=BUTTON_COLOR_LIGHT, fg='#FFFFFF', borderwidth=0, padx=10, pady=5)
theme_button.place(relx=1.0, rely=0.0, anchor='ne')
theme_button.bind("<Enter>", lambda e: theme_button.config(bg=BUTTON_HOVER_COLOR))
theme_button.bind("<Leave>", lambda e: theme_button.config(bg=BUTTON_COLOR_LIGHT))

# Roll Number Input
roll_no_label = Label(root, text="Enter your Roll Number:", anchor="center", font=(FONT, 18))
roll_no_label.pack(pady=20)
roll_no_entry = Entry(root, textvariable=roll_no_var, width=30, justify='center', borderwidth=0, font=(FONT, 20))
roll_no_entry.pack(pady=20)
roll_no_entry.config(bg=ENTRY_BG_COLOR, fg=ENTRY_FG_COLOR)

# Instructions
instructions = Label(root, text="Drag and drop files here or click 'Select Files' to upload.\nIf multiple files are selected, they will be zipped.", font=(FONT, 18), wraplength=750, justify="center")
instructions.pack(pady=20)

# Remove drag-and-drop functionality entirely
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
            zip_file_path = f"{roll_no}.zip"
            zip_files(file_paths, zip_file_path)
            submit_file(zip_file_path, roll_no)
        else:
            submit_file(file_paths[0], roll_no)

# Register drag-and-drop functionality
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

# Select Files Button
select_button = Button(root, text="Select Files", command=lambda: Thread(target=select_files).start(), font=(FONT, 14), bg=BUTTON_COLOR_LIGHT, fg='#FFFFFF', borderwidth=2, padx=15, pady=10)
select_button.pack(pady=30)
select_button.bind("<Enter>", lambda e: select_button.config(bg=BUTTON_HOVER_COLOR))
select_button.bind("<Leave>", lambda e: select_button.config(bg=BUTTON_COLOR_LIGHT))

def create_progress_dialog():
    dialog = Toplevel(root)
    dialog.title("Uploading")
    dialog.geometry("350x250")
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
            zip_file_path = f"{roll_no}.zip"
            zip_files(file_paths, zip_file_path)
            submit_file(zip_file_path, roll_no)
        else:
            submit_file(file_paths[0], roll_no)

def zip_files(file_paths, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))
    print(f"Created zip file: {zip_file_path}")

def submit_file(file_path, roll_no):
    try:
        dialog, progress, progress_label, speed_label, time_label = create_progress_dialog()

        def upload_file():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((server_ip_var.get(), int(server_port_var.get())))
                except ConnectionRefusedError:
                    messagebox.showerror("Connection Error", "Could not connect to the server. Please make sure the server is running.")
                    dialog.destroy()
                    return

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

                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(int(chunk_size_var.get()))
                        if not data:
                            break
                        try:
                            s.sendall(data)
                            total_sent += len(data)
                            elapsed_time = time.time() - start_time
                            speed = total_sent / elapsed_time if elapsed_time > 0 else 0
                            estimated_time = (file_size - total_sent) / speed if speed > 0 else 0
                            progress['value'] = total_sent
                            progress_label['text'] = f"{int((total_sent / file_size) * 100)}%"
                            speed_label['text'] = f"Speed: {speed / 1024:.2f} KB/s"
                            time_label['text'] = f"Time Left: {estimated_time // 60:.0f}m {estimated_time % 60:.0f}s"
                            root.update_idletasks()
                        except ConnectionResetError:
                            messagebox.showerror("Connection Error", "The connection to the server was lost. Please try again.")
                            return

                s.shutdown(socket.SHUT_WR)
                response = s.recv(1024).decode()
                if response == 'ok':
                    messagebox.showinfo("Success", "File uploaded successfully!")
                else:
                    messagebox.showerror("Error", "Failed to upload file.")
                
            finally:
                s.close()
                dialog.destroy()

        Thread(target=upload_file).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

def create_settings_dialog():
    dialog = Toplevel(root)
    dialog.title("Settings")
    dialog.geometry("400x300")
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

    apply_button = Button(dialog, text="Apply", command=apply_settings, font=(FONT, 14), bg=BUTTON_COLOR_LIGHT, fg='#FFFFFF', borderwidth=2, padx=10, pady=5)
    apply_button.pack(pady=5)
    apply_button.bind("<Enter>", lambda e: apply_button.config(bg=BUTTON_HOVER_COLOR))
    apply_button.bind("<Leave>", lambda e: apply_button.config(bg=BUTTON_COLOR_LIGHT))

    center_window(dialog, 400, 300)
    return dialog

def open_settings():
    create_settings_dialog()

# Settings Button
settings_button = Button(root, text="⚙️ Settings", command=open_settings, font=(FONT, 12), bg=BUTTON_COLOR_LIGHT, fg='#FFFFFF', borderwidth=0, padx=10, pady=5)
settings_button.place(relx=1.0, rely=0.0, anchor='ne', x=-120)
settings_button.bind("<Enter>", lambda e: settings_button.config(bg=BUTTON_HOVER_COLOR))
settings_button.bind("<Leave>", lambda e: settings_button.config(bg=BUTTON_COLOR_LIGHT))

def start_app():
    root.mainloop()

if __name__ == "__main__":
    start_app()
