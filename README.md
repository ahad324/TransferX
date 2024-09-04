# 🎓 Student File Submission System

This project is a Python-based file submission system that allows students to submit their assignments via a GUI application. The system consists of a server application and a client application. The server receives files from clients and stores them in a designated folder, while the client allows students to select files, optionally compress them, and send them to the server.

## ✨ Features

### 🖥️ Server Application
- **👨‍💻 GUI Interface:** The server has a user-friendly interface built with Tkinter, displaying logs, active connections, and other relevant information.
- **📂 File Storage:** Files received from clients are saved in the `bucket_storage` directory.
- **📈 Real-time Logs:** The server logs incoming connections, file transfers, and other activities in real-time.
- **⚙️ Customizable Settings:** The server IP, port, and chunk size can be adjusted via the settings tab.

### 💻 Client Application
- **🖼️ GUI Interface:** The client has a simple and intuitive GUI, allowing students to select files for submission.
- **🗜️ File Compression:** Multiple files can be compressed into a single ZIP file before submission.
- **🌗 Theme Toggle:** Users can switch between light and dark themes in the client application.
- **🚀 Progress Tracking:** The client displays a progress bar during file uploads, providing feedback on the submission process.

## 🛠️ Installation

### 📋 Requirements
- Python 3.x
- Required libraries:
  - `socket`
  - `os`
  - `json`
  - `tkinter`
  - `zipfile`
  - `threading`
  - `logging`

Install the required libraries using pip:

```bash
pip install -r requirements.txt
```
## 🚀 Usage

### 🖥️ Running the Server
1. Navigate to the server directory.
2. Run the server application:
    ```bash
    python server.py
    ```
3. The server window will open, displaying the logs, active connections, and settings.

### 💻 Running the Client
1. Navigate to the client directory.
2. Run the client application:
    ```bash
    python client.py
    ```
3. The client window will open, allowing students to select files, choose a theme, and submit their assignments.

### 📤 Submission Process
1. Students select the files they want to submit.
2. Optionally, they can compress the files into a ZIP archive.
3. Click the "Submit" button to send the files to the server.
4. The server will store the files in the `bucket_storage` directory.

## 🎨 Customization

### ⚙️ Server Settings
- The server IP, port, and chunk size can be customized through the settings tab in the server application.

### 🌗 Client Themes
- The client application allows users to toggle between light and dark themes for a personalized experience.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a pull request or report any issues you encounter.
