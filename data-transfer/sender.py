import argparse
import json
import random
import socket
import time

PORT = 5005 # The port identifies the receiving program on a computer.

parser = argparse.ArgumentParser(description="Send CEV telemetry over UDP.")
parser.add_argument("receiver_ip", nargs="?", default="127.0.0.1",
                    help="Receiver IP address; default is this computer")
args = parser.parse_args()

# An IP address identifies a computer and 127.0.0.1 means this computer.
# SOCK_DGRAM selects UDP instead of TCP
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    print(f"Race car -> {args.receiver_ip}:{PORT}. Stop with Ctrl+C.")
    try:
        while True:
            # TODO 1: Generate random values for speed (km/h) between 0 and 100 km/hr, 
            # voltage (V) between 40 and 50 V, battery (%) between 0 and 100.
            speed = random.uniform(0, 100)  
            voltage = random.uniform(40, 50) 
            battery = random.uniform(0, 100)  

            # TODO 2: Store the three readings in a dictionary.
            data = {
                "speed": speed,
                "voltage": voltage,
                "battery": battery
            }

            # TODO 3: Serialize the dictionary to a JSON, then encode as UTF-8 bytes.
            json_data = json.dumps(data).encode('utf-8')
            

            # TODO 4: Send the data to the receiver's IP address and port.
            sock.sendto(json_data, (args.receiver_ip, PORT))

            time.sleep(1)  # Send one new set of readings each second.
    except KeyboardInterrupt:
        print("\nPublisher stopped")
