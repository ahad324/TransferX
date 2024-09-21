import socket
import threading
import logging
import os

# Constants
UDP_PORT, DISCOVER_MSG, RESPONSE_MSG = 55001, "DISCOVER_SERVER", "SERVER_IP"
BASE_DIR, GUI_LOG_CALLBACK, stop_event = None, None, threading.Event()
TIMEOUT = 0.5

def setup_udp_logging():
    if not BASE_DIR: raise RuntimeError("BASE_DIR not set.")    
    os.makedirs(BASE_DIR, exist_ok=True)
    log_file = os.path.join(BASE_DIR, 'udp_connections.log')
    
    udp_logger = logging.getLogger('udp')
    udp_logger.setLevel(logging.INFO)
    
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    udp_logger.addHandler(handler)
    
    return udp_logger

def get_network_ip():
    try:
        # Create a temporary socket to determine the network IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception as e:
        ip = '0.0.0.0'
    finally:
        s.close()
    return ip
# UDP broadcast handling
def handle_udp_broadcast():
    udp_logger = setup_udp_logging()
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.bind(('', UDP_PORT))
    
    server_ip = get_network_ip()
    log_message = lambda msg: (udp_logger.info(msg), GUI_LOG_CALLBACK(msg)) if GUI_LOG_CALLBACK else udp_logger.info(msg)
    log_message(f"📡 UDP broadcast server is running {get_network_ip()}:{UDP_PORT}...")
    
    while not stop_event.is_set():
        try:
            udp_sock.settimeout(TIMEOUT)
            message, addr = udp_sock.recvfrom(1024)
            if message.decode() == DISCOVER_MSG:
                udp_sock.sendto(server_ip.encode(), addr)
                log_message(f"🔍 Discovery from {addr}, responded with {server_ip}")
        except socket.timeout: pass
        except Exception as e: log_message(f"❌ Error in UDP Broadcast: {e}")
    
    log_message("🔴 UDP broadcast server stopped.")
    udp_sock.close()

# Start the UDP listener thread
def start_udp_listener(base_dir, log_callback):
    global BASE_DIR, GUI_LOG_CALLBACK
    BASE_DIR, GUI_LOG_CALLBACK = base_dir, log_callback
    stop_event.clear()  # Reset the stop event
    threading.Thread(target=handle_udp_broadcast, daemon=True).start()

# Stop the UDP listener
def stop_udp_listener(): stop_event.set()