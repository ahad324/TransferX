import socket
import threading
import logging
import os

# Constants
UDP_BROADCAST_PORT = 55001
UDP_DISCOVERY_MESSAGE = "DISCOVER_SERVER"
UDP_RESPONSE_MESSAGE = "SERVER_IP"

# Path to the directory where logs will be stored
BASE_DIR = None  # This will be set by server.py
GUI_LOG_CALLBACK = None  # Callback function to update Tkinter GUI
stop_event = threading.Event()  # Event to signal stopping the UDP listener

def setup_udp_logging():
    if BASE_DIR is None:
        raise RuntimeError("BASE_DIR is not set.")
    
    log_file = os.path.join(BASE_DIR, 'udp_connections.log')
    
    # Ensure the log directory exists
    os.makedirs(BASE_DIR, exist_ok=True)
    
    udp_logger = logging.getLogger('udp')
    udp_logger.setLevel(logging.INFO)
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)
    
    udp_logger.addHandler(file_handler)
    return udp_logger

# UDP broadcast handling
def handle_udp_broadcast():
    udp_logger = setup_udp_logging()
    
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(('', UDP_BROADCAST_PORT))
    
    udp_logger.info("UDP broadcast server is running...")
    
    if GUI_LOG_CALLBACK:
        GUI_LOG_CALLBACK("UDP broadcast server is running...")
    
    while not stop_event.is_set():
        try:
            udp_sock.settimeout(1)  # Short timeout to regularly check stop_event
            message, client_address = udp_sock.recvfrom(1024)
            if message.decode() == UDP_DISCOVERY_MESSAGE:
                server_ip = socket.gethostbyname(socket.gethostname())
                udp_sock.sendto(server_ip.encode(), client_address)
                log_message = f"Sent server IP {server_ip} to {client_address}"
                udp_logger.info(log_message)
                if GUI_LOG_CALLBACK:
                    GUI_LOG_CALLBACK(log_message)
        except socket.timeout:
            # Timeout is used to check stop_event regularly
            pass
        except Exception as e:
            error_message = f"Error in UDP broadcast: {e}"
            udp_logger.error(error_message)
            if GUI_LOG_CALLBACK:
                GUI_LOG_CALLBACK(error_message)
    
    udp_logger.info("UDP broadcast server is stopped.")
    if GUI_LOG_CALLBACK:
        GUI_LOG_CALLBACK("UDP broadcast server is stopped.")
    udp_sock.close()

# Start the UDP listener thread
def start_udp_listener(base_dir, log_callback):
    global BASE_DIR, GUI_LOG_CALLBACK, stop_event
    BASE_DIR = base_dir
    GUI_LOG_CALLBACK = log_callback
    stop_event.clear()  # Reset the stop event
    udp_thread = threading.Thread(target=handle_udp_broadcast)
    udp_thread.daemon = True
    udp_thread.start()

# Stop the UDP listener
def stop_udp_listener():
    stop_event.set()
