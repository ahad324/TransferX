import socket
import time
from zeroconf import ServiceBrowser, Zeroconf

SERVICE_TYPE = "_transferx._tcp.local."
TIMEOUT = 10

class ServerListener:
    def __init__(self):
        self.server_info = None

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            self.server_info = info

    def remove_service(self, zeroconf, type, name):
        pass

    def update_service(self, zeroconf, type, name):
        pass

def verify_connection(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=5):
            return True
    except (socket.timeout, ConnectionRefusedError):
        return False

def discover_server(ip=None, timeout=TIMEOUT, stop_event=None):
    if ip:
        # If IP is provided, verify the connection
        if verify_connection(ip, 5000):
            return {"status": "success", "server_ip": ip, "server_port": 5000}
        else:
            return {"status": "error", "message": f"Could not connect to server at {ip}:5000"}

    zeroconf = Zeroconf()
    listener = ServerListener()
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if stop_event and stop_event.is_set():
            zeroconf.close()
            return None
        if listener.server_info:
            ip = socket.inet_ntoa(listener.server_info.addresses[0])
            port = listener.server_info.port
            zeroconf.close()
            return {"status": "success", "server_ip": ip, "server_port": port}
        time.sleep(0.1)
    
    zeroconf.close()
    return {"status": "error", "message": "No server found. Please check your network settings."}