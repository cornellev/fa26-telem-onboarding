# Data Transfer Workshop: UDP

In this coding activity, you will work in pairs to build a real-time telemetry system that sends simulated race car sensor readings between two computers using Python and UDP. 
- **Sender (`sender.py`):** Simulates the car and sends sensor readings
- **Receiver (`receiver.py`):** Simulates the pit and displays incoming sensor readings

## Setup
We will use [Python 3](https://www.python.org/downloads/)'s built in libraries. To verify that  Python is installed, open a terminal and run:

**macOS:**
```bash
python3 --version
```

**Windows:**
```bash
python --version
```

## Background

Recall that our telemetry system follows these steps:

1. **Data Collection:** Get sensor readings from the car.
2. **Serialization:** Convert sensor data into a format that can be transmitted (in our case, bits).
3. **Transmission:** Send data from the car to the pit.
4. **Reception:** Receive the transmitted data.
5. **Deserialization:** Convert the binary data back into sensor readings.
6. **Visualization:** Display the sensor readings.

For this workshop, we will use JSON instead of Protobuf for (de)serialization, and UDP to send the data. Below are a couple of helpful definitions for this activity: 
- **UDP** sends individual packets without establishing a connection or guaranteeing that the receiver receives the packets
- An **IP address** identifies the computer that is receiving data (starter code uses `5005`)
- A **port** identifies the receiving program on the receiving computer (starter code uses `5005`)

At a high level, because UDP sends bytes, the sender will convert a Python dictionary into JSON and encode it as UTF-8 bytes. The receiver will reverse these steps.

## Instructions

### 1. Set up your Git branch
One person will implement `sender.py`, and the other will implement `receiver.py`. If you have not already, clone the repository:

```bash
git clone https://github.com/cornellev/fa26-telem-onboarding
cd fa26-telem-onboarding
cd data-transfer
```

Create and push a new branch for you and your partner.

### 2. Data message format 
We will be using this schema for the data packets:

| Key | Type | Sensor Reading | Range |
|---|--- | ---|---|
| `speed` | `float` | Speed (km/h) | 0–100 |
| `voltage` |  `float` | Battery voltage (V) | 300–400 |
| `battery` |  `float` | Battery charge (%) | 0–100 |

Example JSON message:

```json
{"speed": 42.3, "voltage": 367.8, "battery": 82.1}
```

The sender will generate random readings, and the receiver will decode and print them. 

### 3. Complete the TODOs 

Each starter file has four TODOs for you to implement. The socket setup is already provided.

#### Sender (`sender.py`)
Your goal is to generate and send one new set of readings every second.
1. **TODO 1: Generate readings.** Use `random.uniform(low, high)` to generate random values for `speed`, `voltage`, and `battery` within the ranges above. You can use `round(value, 1)` to keep one decimal place, if you'd like.
2. **TODO 2: Create a dictionary.** Store the sensor readings in a dictionary with the keys `speed`, `voltage`, and `battery`.
3. **TODO 3: Serialize the dictionary.** Use `json.dumps()` to convert the dictionary to a JSON string, then call `.encode("utf-8")` to convert it into bytes.
4. **TODO 4: Send the serialized data.** Use `sock.sendto()` to send those bytes to `(args.receiver_ip, PORT)`.

Keep `time.sleep(1)` in the loop for now, so that the sender publishes at 1 Hz (i.e. once per second). 

#### Receiver (`receiver.py`)
Your goal is to receiver the data and display the readings. 
1. **TODO 1: Receive the incoming data.** Use `sock.recvfrom(BUFFER_SIZE)` to get both the incoming bytes and sender address.
2. **TODO 2: Deserialize the data.** Decode the bytes using `.decode("utf-8")`, then use `json.loads()` to reconstruct the JSON dictionary.
3. **TODO 3: Extract the sensor readings.** Read `speed`, `voltage`, and `battery` from the dictionary.
4. **TODO 4: Display the data.** Print all three readings with their units. Use `flush=True` to display the output immediately. An example output should look something like this: 
```text
Speed: 42.3 km/h | Voltage: 46.8 V | Battery: 82.1%
```

### 4. Combine your code and test locally
Push and pull your changes so you both have the completed `sender.py` and `receiver.py` files. 

We are first going to test the two programs on **one computer**. Open two terminals in the repository folder (use `python3` instead if needed):
```bash
# Terminal 1 (receiver)
python receiver.py
```
```bash
# Terminal 2 (sender)
python sender.py
```
You should see a new set of sensor readings printed by the receiver approximately every second! Use `Ctrl+C` to stop either program.

### 5. Test between two computers
Once your local test works, let's try sending data from one laptop to the other!
1. Connect both laptops to the same network (e.g. RedRover). 
2. Find the receiver laptop's IP address:
    - macOS: System settings -> Wi-Fi -> Details -> TCP/IP
    - Windows: Run `ipconfig` and find the IPv4 Address for your active Wi-Fi adapter
3. On the receiver laptop, run `python receiver.py`.
4. On the sender laptop, run `python sender.py [receiver IP address]`.

You can now verify to see if the receiver prints readings from the sender laptop!

## Bonus Challenges
1. **Protobuf:** Our actual telemetry system uses [Protobuf](https://protobuf.dev/) to (de)serialize, rather than JSON. Try changing the sender and receiver to (de)serialize packets using a Protobuf message definition instead! (Hint: The Protobuf website should have very detailed instructions on how to do this.)
2.  **Latency:** Recall that in an ideal setting, we would like to minimize latency (i.e. the delay between sending and receiving the data) in our system. Measure how long it takes for the data to get from the sender to the receiver. (Hint: Consider adding a timestamp to each message and comparing it with the receiver's time.)
3. **Publishing frequency:** The starter code publishes at 1 Hz. Increase the frequency to 10 Hz, 50 Hz, and 100 Hz. Can the receiver keep up at each frequency?
