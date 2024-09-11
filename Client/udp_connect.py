import socket

BROADCAST_PORT = 55001
BROADCAST_MESSAGE = "DISCOVER_SERVER"

def discover_server_ip(timeout=5):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udp_sock.settimeout(timeout)

    broadcast_address = ('<broadcast>', BROADCAST_PORT)

    try:
        # Send a UDP broadcast message
        udp_sock.sendto(BROADCAST_MESSAGE.encode(), broadcast_address)

        # Wait for a response from the server
        while True:
            try:
                response, server_address = udp_sock.recvfrom(1024)
                server_ip = response.decode()
                return server_ip
            except socket.timeout:
                return None
    finally:
        udp_sock.close()