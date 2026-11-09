# Data Transfer Workshop: UDP

In this coding activity, you'll build a real-time telemetry system that sends simulated race car sensor readings from one computer to another using Python and UDP.

You'll work in pairs:
- **Sender (`sender.py`):** Simulates the race car and transmits sensor readings.
- **Receiver (`receiver.py`):** Simulates the pit crew and displays incoming telemetry.

You'll work on the **same Git branch** as your partner, implementing separate files before combining your code and testing the system.

**Duration:** Approximately 40 minutes

## Setup

You'll need:
- Python 3 ([download here](https://www.python.org/downloads/))
- Git ([download here](https://git-scm.com/downloads))
- The workshop repository

No additional Python packages are required.

To verify that Python is installed, open a terminal and run:

**macOS:**
```bash
python3 --version
```

**Windows:**
```bash
python --version
```

To verify Git is installed:

```bash
git --version
```

## Background

### Telemetry System

Recall that our telemetry system follows these steps:

1. **Data Collection:** Get sensor readings from the car.
2. **Serialization:** Convert sensor data into a format suitable for transmission.
3. **Transmission:** Send the data to the pit crew.
4. **Reception:** Receive the transmitted data.
5. **Deserialization:** Reconstruct the original data.
6. **Storage & Visualization:** Store and display the sensor readings.

For simplicity, we'll use **JSON instead of Protobuf** for serialization and deserialization, since JSON is built into Python. We'll use **UDP** to transmit data between computers.

Our workshop follows this pipeline:

**Data Generation → JSON Serialization → UDP Transmission → Reception → JSON Deserialization → Display**

### UDP Basics

A few networking concepts to know:

- **IP Address:** Identifies the computer we're sending data to.
- **Port:** Identifies the program receiving the data. We'll use port `5005`.
- **UDP (User Datagram Protocol):** Transmits data in individual packets called *datagrams*. Unlike TCP, UDP doesn't establish a connection or guarantee packet delivery or ordering.

Since UDP transmits bytes, we'll convert our Python dictionary into JSON text, then encode it into bytes. The receiver reverses these steps to recover the original dictionary.

## 1. Set Up Your Git Branch (5 minutes)

You'll be working on the **same Git branch** as your partner, but each of you will implement a different file.

**Step 1: Clone the repository**

If you haven't already, clone the workshop repository:

```bash
git clone <repository-url>
cd udp-telemetry-workshop
```

Replace `<repository-url>` with the GitHub repository URL provided by the instructor.

**Step 2: Create a branch for your pair**

One person creates a new branch and pushes it to GitHub:

```bash
git switch -c udp-telemetry-team1
git push -u origin udp-telemetry-team1
```

Replace `team1` with your pair's assigned team number.

**Step 3: Have your partner switch to the same branch**

Your partner runs:

```bash
git fetch origin
git switch --track origin/udp-telemetry-team1
```

**Step 4: Assign roles**

Decide who will implement `sender.py` and who will implement `receiver.py`.

Both partners should work on the same branch, but **only edit your assigned file** to avoid merge conflicts.

## 2. Understand the Telemetry Message (5 minutes)

We've already defined the telemetry message format you'll use for this activity. Both the sender and receiver will follow the same JSON structure so they agree on what data is being transmitted.

Your messages will contain the following sensor readings:

| Key | Sensor Reading | Simulated Range |
|---|---|---|
| `speed` | Speed (km/h) | 0–100 |
| `voltage` | Battery voltage (V) | 300–400 |
| `battery` | Battery charge (%) | 0–100 |

Example JSON message:

```json
{"speed": 42.3, "voltage": 367.8, "battery": 82.1}
```

The sender will generate random values for these fields, and the receiver will decode and display them.

## 3. Complete the TODOs (15 minutes)

Each starter file contains TODOs for you to implement. The socket setup and cleanup are already provided, so you can focus on the telemetry pipeline.

Replace the `pass` statements with your code. In `receiver.py`, also replace the `raise NotImplementedError(...)` statement.

### Student A: Sender (`sender.py`)

Your goal is to generate simulated sensor readings and transmit them once per second.

**TODO 1: Generate sensor readings**

Inside the loop, generate three random values:
- `speed`: Between 0 and 100
- `voltage`: Between 300 and 400
- `battery`: Between 0 and 100

Use `random.uniform(low, high)` to generate random decimal values and `round(value, 1)` to round them to one decimal place.

**TODO 2: Create a telemetry dictionary**

Store the readings in a dictionary named `telemetry`, using the keys `speed`, `voltage`, and `battery`.

Remember that Python dictionaries use the following syntax:

```python
{"key": value, "another_key": value}
```

**TODO 3: Serialize the data**

Convert the dictionary into JSON using `json.dumps()`, then encode the resulting string into bytes using `.encode("utf-8")`.

Store the result in a variable named `message`.

**TODO 4: Transmit the message**

Use the UDP socket to send your message:

```python
sock.sendto(message, (args.receiver_ip, PORT))
```

The destination consists of the receiver's IP address and port.

Keep `time.sleep(1)` so the sender transmits approximately once per second.

### Student B: Receiver (`receiver.py`)

Your goal is to receive incoming telemetry, reconstruct the data, and display the readings.

**TODO 1: Receive incoming data**

Use `sock.recvfrom(BUFFER_SIZE)` to receive a UDP packet.

This returns two values:
- `data`: The received bytes.
- `sender_address`: The sender's IP address and port.

Store both values in their corresponding variables.

**TODO 2: Deserialize the data**

First, decode the received bytes into a string using:

```python
data.decode("utf-8")
```

Then convert the JSON string back into a Python dictionary using `json.loads()`.

Store the resulting dictionary in `telemetry`.

**TODO 3: Extract sensor readings**

Retrieve the speed, voltage, and battery readings from the dictionary.

For example:

```python
speed = telemetry["speed"]
```

**TODO 4: Display the telemetry**

Print all three readings, including their units, on one line using an f-string.

For example:

```text
Speed: 42.3 km/h | Voltage: 367.8 V | Battery: 82.1%
```

Use `flush=True` in your `print()` call to display each reading immediately.

If you get stuck, refer to the corresponding file in the `solutions/` folder.

## 4. Combine Your Code and Test Locally (5 minutes)

Once you've both completed your TODOs, push your changes to your shared Git branch so both laptops have the completed sender and receiver files.

### Step 1: Commit and push the first student's code

The sender student runs:

```bash
git add sender.py
git commit -m "Implement UDP telemetry sender"
git push
```

### Step 2: Pull, commit, and push the second student's code

After the sender has pushed, the receiver student runs:

```bash
git pull
git add receiver.py
git commit -m "Implement UDP telemetry receiver"
git push
```

### Step 3: Sync both laptops

The sender student runs:

```bash
git pull
```

Now both laptops should have the completed `sender.py` and `receiver.py`.

### Step 4: Test on one computer

Before transmitting data between laptops, test both programs locally.

Open two terminals in the `udp-telemetry-workshop` directory.

**Terminal 1: Start the receiver**

```bash
python receiver.py
```

**Terminal 2: Start the sender**

```bash
python sender.py
```

On macOS, use `python3` instead of `python` if needed.

By default, the sender transmits to `127.0.0.1`, also known as **localhost**, which refers to the same computer.

If everything works, your receiver should display something like:

```text
Pit crew listening on port 5005. Stop with Ctrl+C.

Speed: 42.3 km/h | Voltage: 367.8 V | Battery: 82.1%
Speed: 57.6 km/h | Voltage: 352.4 V | Battery: 79.5%
Speed: 63.1 km/h | Voltage: 381.2 V | Battery: 76.8%
```

You should see a new reading approximately every second.

Press `Ctrl+C` in both terminals to stop the programs.

## 5. Connect Two Laptops (5 minutes)

Now that your code works locally, try transmitting telemetry between your laptops.

**Step 1: Connect to the same network**

Connect both laptops to **RedRover (Cornell Wi-Fi)**.

Being on the same Wi-Fi network doesn't necessarily mean devices can communicate directly. If RedRover blocks device-to-device traffic, you can continue testing using localhost or use an instructor-approved alternative network.

**Step 2: Find the receiver's IP address**

On the receiver's computer:

- **macOS:** Open System Settings → Wi-Fi → Details → TCP/IP and find the IP address.
- **Windows:** Open PowerShell or Command Prompt, run `ipconfig`, and find the IPv4 Address under your active Wi-Fi adapter.

**Step 3: Start the receiver**

On the receiver's laptop, run:

```bash
python receiver.py
```

**Step 4: Start the sender**

On the sender's laptop, run:

```bash
python sender.py 192.168.1.42
```

Replace `192.168.1.42` with the receiver's actual IP address.

The receiver is configured to listen on `0.0.0.0`, which means it accepts packets arriving through any local network interface. Do not use `0.0.0.0` as the sender's destination.

**Step 5: Verify the connection**

If everything is working, the receiver should display updated sensor readings from the sender's computer.

**Note:** If localhost works but the two-laptop test doesn't, the issue may be network isolation rather than your code.

## Troubleshooting

| Problem | What to Check |
|---|---|
| No readings appear | Make sure the receiver is running, the TODOs are complete, and the IP address and port match. |
| Localhost works, but two laptops don't | RedRover may restrict device-to-device communication. Try an instructor-approved alternative network or continue locally. |
| `Address already in use` | Another receiver may already be using port `5005`. Stop it before restarting. |
| `KeyError` or JSON error | Make sure both programs use the same dictionary keys and serialization format. |
| Git push rejected | Commit your local changes if necessary, run `git pull` to incorporate your partner's changes, resolve any conflicts, and push again. |
| Python command not found | Try `python3` on macOS or `py -3` on Windows. |

If prompted by your operating system, allow Python to communicate on a trusted private network. Do not disable your firewall.

## 6. Discussion and Bonus Challenge (5 minutes)

Walk through the data-transfer pipeline with your partner and identify where each step occurs in your code.

Consider these questions:

1. Why do we need to serialize the sensor readings before transmitting them?
2. What's the difference between an IP address and a port?
3. What happens when the receiver is waiting for a packet?
4. What happens to packets sent while the receiver isn't running?
5. Why might UDP be useful for real-time telemetry despite not guaranteeing delivery?

### Bonus: Detect Missing Packets

If you have extra time, try adding sequence numbers to your telemetry messages.

On the sender, add a `sequence` field that increases by one for every generated message. On the receiver, track the highest sequence number received and look for gaps.

For example:

```text
Received packet #1
Received packet #2
Received packet #4
Warning: Packet #3 may be missing!
```

To test your implementation, deliberately skip transmitting every fifth message while continuing to increment the sequence number.

Sequence numbers help detect missing or out-of-order packets, but they don't guarantee delivery.
