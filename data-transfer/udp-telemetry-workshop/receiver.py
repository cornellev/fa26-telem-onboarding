"""CEV pit crew: complete the four TODOs, then run python receiver.py."""

import json
import socket

PORT = 5005  # Must match the sender's destination port.
BUFFER_SIZE = 4096  # Maximum bytes to receive; plenty for our small JSON message.

# UDP receives independent datagrams (messages), one recvfrom() call at a time.
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    # 0.0.0.0 listens on all local network interfaces, including localhost.
    sock.bind(("0.0.0.0", PORT))
    print(f"Pit crew listening on port {PORT}. Stop with Ctrl+C.")
    try:
        while True:
            # TODO 1: Receive bytes and the sender address with recvfrom().
            # Replace this exception with your receiving code.
            raise NotImplementedError("Complete the receiver TODOs first.")

            # TODO 2: Decode UTF-8 bytes, then deserialize JSON into telemetry.
            pass

            # TODO 3: Extract speed, voltage, and battery from telemetry.
            pass

            # TODO 4: Print the readings with labels, units, and one decimal.
            pass
    except KeyboardInterrupt:
        print("\nPit crew stopped.")
