from zeroconf import ServiceBrowser, Zeroconf
import socket
import time

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

def discover_server(ip=None, timeout=TIMEOUT):
    if ip:
        # If IP is provided, return it directly
        return {"status": "success", "server_ip": ip, "server_port": 5000}  # Assuming default port 5000

    zeroconf = Zeroconf()
    listener = ServerListener()
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener)
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if listener.server_info:
            ip = socket.inet_ntoa(listener.server_info.addresses[0])
            port = listener.server_info.port
            zeroconf.close()
            return {"status": "success", "server_ip": ip, "server_port": port}
        time.sleep(0.1)
    
    zeroconf.close()
    return {"status": "error", "message": "No server found. Please check your network settings."}