"""Complete 4 TODO's and run receiver.py"""

import json
import socket
PORT = 5005  # Must match the sender's port (identifies the sender's program on a computer).
BUFFER_SIZE = 4096  # Maximum bytes we expect to receive

# Create a UDP socket 
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    # SOCK_DGRAM selects UDP instead of TCP
    # 0.0.0.0 listens on all local network interfaces
    sock.bind(("0.0.0.0", PORT))
    print(f"Receiver listening on port {PORT}. Stop with Ctrl+C.")
    try:
        while True:
            # TODO 1: Get both the data and the sender address using recvfrom().
            # Replace this exception with your code.
            bytesData, addr = sock.recvfrom(BUFFER_SIZE)


            # TODO 2: Decode the UTF-8 bytes into a JSON string, then convert JSON back into a Python dictionary.
            json_string = bytesData.decode("utf-8")
            data = json.loads(json_string)

            # TODO 3: Extract the speed, voltage, and battery from the dictionary.
            speed = data["speed"]
            voltage = data["voltage"]
            battery = data["battery"]

            # TODO 4: Print the readings to the terminal
            print(f"Speed: {speed}, Voltage: {voltage}, Battery: {battery} (from {addr})")
            
    except KeyboardInterrupt:
        print("Receiver stopped")
