import socket

UDP_IP = "0.0.0.0"
UDP_PORT = 4210  # Match the port used by your robot SDK

print(f"Starting UDP robot simulator on {UDP_IP}:{UDP_PORT}")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

try:
    while True:
        data, addr = sock.recvfrom(1024)
        print(f"Received from {addr}: {data.decode(errors='ignore')}")
        # Always reply with "OK" for testing
        sock.sendto(b"OK", addr)
        print(f"Sent 'OK' to {addr}")
except KeyboardInterrupt:
    print("Simulator stopped.")
finally:
    sock.close()