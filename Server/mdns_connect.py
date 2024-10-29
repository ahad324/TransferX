from zeroconf import ServiceInfo, Zeroconf
import socket
import threading
import logging
import os

# Constants
SERVICE_TYPE = "_transferx._tcp.local."
SERVICE_NAME = "TransferX Server._transferx._tcp.local."
BASE_DIR, GUI_LOG_CALLBACK, stop_event = None, None, threading.Event()

def setup_mdns_logging():
    if not BASE_DIR:
        raise RuntimeError("BASE_DIR not set.")    
    os.makedirs(BASE_DIR, exist_ok=True)
    log_file = os.path.join(BASE_DIR, 'mdns_connections.log')
    
    mdns_logger = logging.getLogger('mdns')
    mdns_logger.setLevel(logging.INFO)
    
    handler = logging.FileHandler(log_file, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    mdns_logger.addHandler(handler)
    
    return mdns_logger

def get_network_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '0.0.0.0'
    finally:
        s.close()
    return ip

def log_message(msg):
    if GUI_LOG_CALLBACK:
        GUI_LOG_CALLBACK(msg)
    # print(msg)

class ServerZeroconf(Zeroconf):
    def __init__(self, logger_func, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger_func = logger_func

    def register_service(self, info, ttl=None, allow_name_change=False):
        super().register_service(info, ttl, allow_name_change)
        self.logger_func(f"🔍 Registered service: {info.name} on {info.server}:{info.port}")

    def unregister_service(self, info):
        super().unregister_service(info)
        self.logger_func(f"🔴 Unregistered service: {info.name}")

    def close(self):
        super().close()
        self.logger_func("🔴 mDNS server stopped.")

def start_mdns_server(port):
    mdns_logger = setup_mdns_logging()
    ip_address = get_network_ip()
    info = ServiceInfo(
        SERVICE_TYPE,
        SERVICE_NAME,
        addresses=[socket.inet_aton(ip_address)],
        port=port,
        properties={},
        server=f"{socket.gethostname()}.local."
    )

    log_func = lambda msg: (mdns_logger.info(msg), GUI_LOG_CALLBACK(msg)) if GUI_LOG_CALLBACK else mdns_logger.info(msg)
    zeroconf = ServerZeroconf(log_func)

    zeroconf.register_service(info)
    log_func(f"✅ mDNS server is running on {ip_address}:{port}")

    return zeroconf, info

def stop_mdns_server(zeroconf, info):
    if zeroconf and info:
        zeroconf.unregister_service(info)
        zeroconf.close()
    else:
        log_message("⚠️ mDNS server was not properly initialized")

# Start the mDNS server
def start_mdns_listener(base_dir, log_callback, port):
    global BASE_DIR, GUI_LOG_CALLBACK
    BASE_DIR, GUI_LOG_CALLBACK = base_dir, log_callback
    stop_event.clear()  # Reset the stop event
    return start_mdns_server(port)

# Stop the mDNS server
def stop_mdns_listener(zeroconf, info):
    stop_event.set()
    stop_mdns_server(zeroconf, info)