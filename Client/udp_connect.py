import socket

BROADCAST_PORT = 55001
BROADCAST_MESSAGE = "DISCOVER_SERVER"
TIMEOUT = 10

def discover_server(ip=None, timeout=TIMEOUT):
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.settimeout(timeout)

    # If no IP is provided, use broadcast, otherwise send to a specific server
    if ip is None:
        udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        target_address = ('<broadcast>', BROADCAST_PORT)
    else:
        target_address = (ip, BROADCAST_PORT)

    try:
        # Send a UDP message (broadcast or direct to a server)
        udp_sock.sendto(BROADCAST_MESSAGE.encode(), target_address)

        # Wait for a response from the server
        while True:
            try:
                response, server_address = udp_sock.recvfrom(1024)
                server_ip = response.decode()
                return {"status": "success", "server_ip": server_ip}
            except socket.timeout:
                return {"status": "error", "message": "Connection timed out. Please check your network settings."}
            except socket.error as e:
                return {"status": "error", "message": f"Socket error: {str(e)}"}
    except socket.error as e:
        return {"status": "error", "message": f"Socket initialization error: {str(e)}"}
    finally:
        udp_sock.close()
