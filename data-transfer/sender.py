"""CEV race car: complete the four TODOs, then run python sender.py [IP]."""

import argparse
import json
import random
import socket
import time

PORT = 5005  # A port identifies the receiving program on a computer.
parser = argparse.ArgumentParser(description="Send CEV telemetry over UDP.")
parser.add_argument("receiver_ip", nargs="?", default="127.0.0.1",
                    help="Pit crew's IP address; default is this computer")
args = parser.parse_args()

# An IP address identifies a computer; 127.0.0.1 means this computer.
# SOCK_DGRAM selects UDP: independent messages without delivery/order guarantees.
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    print(f"Race car -> {args.receiver_ip}:{PORT}. Stop with Ctrl+C.")
    try:
        while True:
            # TODO 1: Generate speed (km/h), voltage (V), battery (%).
            pass

            # TODO 2: Store them in a dictionary named telemetry.
            pass

            # TODO 3: Serialize to JSON text, then encode as UTF-8 bytes.
            pass

            # TODO 4: Send the bytes to (args.receiver_ip, PORT) with sendto().
            pass

            time.sleep(1)  # One new set of readings each second.
    except KeyboardInterrupt:
        print("\nRace car stopped.")
