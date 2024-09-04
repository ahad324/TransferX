import socket
import os
import json
import zipfile
from tkinter import Tk, Button, filedialog, messagebox, Label, Entry, StringVar, ttk, Toplevel
from threading import Thread

# Constants
DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 9999
DEFAULT_CHUNK_SIZE = 4096
DELIMITER = "---END-HEADER---"
FONT = 'Seoge UI'
# Courier New, Consolas, Monaco (popular on Mac OS),
# DejaVu Sans Mono, Fira Code
# Georgia

# Initialize the root window
root = Tk()
root.title("Student File Submission")

# Tkinter Variables
server_ip_var = StringVar(value=DEFAULT_SERVER_IP)
server_port_var = StringVar(value=DEFAULT_SERVER_PORT)
chunk_size_var = StringVar(value=DEFAULT_CHUNK_SIZE)
roll_no_var = StringVar()

def initialize_settings():
    # Initial setup of settings variables if needed
    pass

# Set the initial window size
root.geometry("700x500")  # Initial size for more space
root.minsize(700, 500)  # Minimum size to prevent it from being too small

# Styling
style = ttk.Style()
style.configure('TButton', font=(FONT, 12), padding=10, relief='raised')
style.configure('TLabel', font=(FONT, 16), padding=10, relief='raised')  # Larger font for labels
style.configure('TEntry', font=(FONT, 18), padding=10, relief='raised')  # Larger font for entry
style.configure('TProgressbar', thickness=30, troughcolor='#D3D3D3')  # Increased thickness for progress bar

def set_light_theme():
    root.tk_setPalette(background='#FFFFFF', foreground='#000000')
    style.configure('TButton', background='#0078D4', foreground='#FFFFFF')
    style.configure('TLabel', background='#FFFFFF', foreground='#000000')
    style.configure('TEntry', background='#3C3C3C', foreground='#000000')
    style.configure('TProgressbar', background='#0078D4', troughcolor='#D3D3D3')

def set_dark_theme():
    root.tk_setPalette(background='#2E2E2E', foreground='#FFFFFF')
    style.configure('TButton', background='#1E1E1E', foreground='#FFFFFF')
    style.configure('TLabel', background='#2E2E2E', foreground='#FFFFFF')
    style.configure('TEntry', background='#3C3C3C', foreground='#000000')  # Ensure text is white
    style.configure('TProgressbar', background='#1E1E1E', troughcolor='#3C3C3C')
    
    # Ensure all Entry widgets have black text
    root.option_add('*TEntry.foreground', '#000000')  # Apply black text to all Entry widgets

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

def center_window():
    window_width = root.winfo_reqwidth()
    window_height = root.winfo_reqheight()
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f'{window_width}x{window_height}+{position_right}+{position_top}')

# Center the window initially
root.after(100, center_window)

# To center the app always
# root.bind("<Configure>", center_window)  

# Theme Toggle Button
theme_button = Button(root, text="🌙", command=toggle_theme, font=(FONT, 12), bg='#0078D4', fg='#FFFFFF', relief='raised', borderwidth=0, padx=10, pady=5)
theme_button.place(relx=1.0, rely=0.0, anchor='ne')
theme_button.bind("<Enter>", lambda e: theme_button.config(bg='#0056A0'))
theme_button.bind("<Leave>", lambda e: theme_button.config(bg='#0078D4'))

# Roll Number Input
roll_no_label = Label(root, text="Enter your Roll Number:", anchor="center", font=(FONT, 18))
roll_no_label.pack(pady=20)
roll_no_entry = Entry(root, textvariable=roll_no_var, width=30, justify='center', borderwidth=2, relief='raised', font=(FONT, 20))
roll_no_entry.pack(pady=20)
roll_no_entry.config(bg='#F3F3F3', fg='#000000', highlightbackground='#C1C1C1', highlightcolor='#C1C1C1')

# Instructions
instructions = Label(root, text="Please select your files for submission.\nIf multiple files are selected, they will be zipped.", font=(FONT, 18), wraplength=650, justify="center")
instructions.pack(pady=20)

# Select Files Button
select_button = Button(root, text="Select Files", command=lambda: Thread(target=select_files).start(), font=(FONT, 14), bg='#0078D4', fg='#FFFFFF', relief='raised', borderwidth=2, padx=10, pady=10)
select_button.pack(pady=30)
select_button.config(highlightbackground='#0078D4', highlightcolor='#0078D4')

def create_progress_dialog():
    dialog = Toplevel(root)
    dialog.title("Uploading")
    dialog.geometry("300x150")  # Size of the dialog
    dialog.transient(root)  # Make dialog stay on top of main window
    dialog.grab_set()  # Make dialog modal

    label = Label(dialog, text="Uploading...", font=(FONT, 14))
    label.pack(pady=10)

    progress = ttk.Progressbar(dialog, orient="horizontal", mode="determinate", length=250, style='TProgressbar')
    progress.pack(pady=10)

    progress_label = Label(dialog, text="0%", font=(FONT, 14))
    progress_label.pack(pady=10)

    # Center the dialog on the screen
    dialog.update_idletasks()
    dialog_width = dialog.winfo_width()
    dialog_height = dialog.winfo_height()
    screen_width = dialog.winfo_screenwidth()
    screen_height = dialog.winfo_screenheight()
    position_top = int(screen_height / 2 - dialog_height / 2)
    position_right = int(screen_width / 2 - dialog_width / 2)
    dialog.geometry(f'{dialog_width}x{dialog_height}+{position_right}+{position_top}')

    return dialog, progress, progress_label

def select_files():
    file_paths = filedialog.askopenfilenames()
    if file_paths:
        roll_no = roll_no_var.get().strip()
        if not roll_no:
            messagebox.showerror("Error", "Roll Number is required")
            return

        if len(file_paths) > 1:
            # Zip multiple files and use roll number as the name
            zip_file_path = f"{roll_no}.zip"
            zip_files(file_paths, zip_file_path)
            submit_file(zip_file_path, roll_no)
        else:
            # Single file, no zipping needed
            submit_file(file_paths[0], roll_no)

def zip_files(file_paths, zip_file_path):
    with zipfile.ZipFile(zip_file_path, 'w') as zipf:
        for file in file_paths:
            zipf.write(file, os.path.basename(file))
    print(f"Created zip file: {zip_file_path}")

def submit_file(file_path, roll_no):
    try:
        dialog, progress, progress_label = create_progress_dialog()

        def upload_file():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    s.connect((server_ip_var.get(), int(server_port_var.get())))
                except ConnectionRefusedError:
                    messagebox.showerror("Connection Error", "Could not connect to the server. Please make sure the server is running.")
                    dialog.destroy()  # Close the progress dialog
                    return

                filename = f"{roll_no}.zip" if file_path.endswith('.zip') else f"{roll_no}{os.path.splitext(file_path)[1]}"
                file_size = os.path.getsize(file_path)
                print(f"File size: {file_size} bytes")

                # Create metadata header
                metadata = {
                    "filename": filename,
                    "file_size": file_size,
                }
                metadata_json = json.dumps(metadata)

                # Send metadata and file data separated by delimiter
                header = f"{metadata_json}\n{DELIMITER}\n"
                s.sendall(header.encode())
                print("Header sent")

                # Configure the progress bar
                progress['maximum'] = file_size
                progress['value'] = 0
                total_sent = 0

                with open(file_path, 'rb') as f:
                    while True:
                        data = f.read(int(chunk_size_var.get()))
                        if not data:
                            break
                        s.sendall(data)
                        total_sent += len(data)
                        progress['value'] = total_sent
                        progress_label['text'] = f"{int((total_sent / file_size) * 100)}%"
                        root.update_idletasks()  # Update the progress bar and label

                # Ensure all data is sent
                s.shutdown(socket.SHUT_WR)

                # Receive acknowledgment from the server
                response = s.recv(1024).decode()
                if response == 'success':
                    messagebox.showinfo("Success", "File uploaded successfully!")
                else:
                    messagebox.showerror("Error", "Failed to upload file.")
                
                select_button.config(state='normal')
            finally:
                s.close()
                dialog.destroy()

        Thread(target=upload_file).start()

    except Exception as e:
        messagebox.showerror("Error", str(e))

def create_settings_dialog():
    dialog = Toplevel(root)
    dialog.title("Settings")
    dialog.geometry("400x300")  # Size of the dialog
    dialog.transient(root)  # Make dialog stay on top of main window
    dialog.grab_set()  # Make dialog modal

    def apply_settings():
        try:
            new_ip = ip_entry.get()
            new_port = int(port_entry.get())
            new_chunk_size = int(chunk_size_entry.get())

            # Validate IP, port, and chunk size
            if not is_valid_ip(new_ip):
                raise ValueError("Invalid IP address")
            if not is_valid_port(new_port):
                raise ValueError("Port number must be between 0 and 65535")
            if not is_valid_chunk_size(new_chunk_size):
                raise ValueError("Chunk size must be a positive integer")

            # Update variables
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

    # IP Entry
    Label(dialog, text="Server IP:", font=(FONT, 12)).pack(pady=5)
    ip_entry = Entry(dialog, font=(FONT, 12))
    ip_entry.insert(0, server_ip_var.get())  # Set the initial value
    ip_entry.pack(pady=5)

    # Port Entry
    Label(dialog, text="Server Port:", font=(FONT, 12)).pack(pady=5)
    port_entry = Entry(dialog, font=(FONT, 12))
    port_entry.insert(0, server_port_var.get())  # Set the initial value
    port_entry.pack(pady=5)

    # Chunk Size Entry
    Label(dialog, text="Chunk Size:", font=(FONT, 12)).pack(pady=5)
    chunk_size_entry = Entry(dialog, font=(FONT, 12))
    chunk_size_entry.insert(0, chunk_size_var.get())  # Set the initial value
    chunk_size_entry.pack(pady=5)

    # Apply Button
    apply_button = Button(dialog, text="Apply", command=apply_settings, font=(FONT, 12), bg='#0078D4', fg='#FFFFFF', relief='raised', borderwidth=2, padx=10, pady=5)
    apply_button.pack(pady=20)

    return dialog

def open_settings():
    create_settings_dialog()

# Settings Button
settings_button = Button(root, text="⚙️ Settings", command=open_settings, font=(FONT, 12), bg='#0078D4', fg='#FFFFFF', relief='raised', borderwidth=0, padx=10, pady=5)
settings_button.place(relx=1.0, rely=0.0, anchor='ne', x=-100)  # Adjust position as needed
settings_button.bind("<Enter>", lambda e: settings_button.config(bg='#0056A0'))
settings_button.bind("<Leave>", lambda e: settings_button.config(bg='#0078D4'))

def start_app():
    root.mainloop()

if __name__ == "__main__":
    start_app()
