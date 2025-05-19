import socket
import struct
import json
import os

# Define the JSON file path
JSON_FILE_PATH = 'telemetry_data.json'

# Delete the JSON file if it already exists
if os.path.exists(JSON_FILE_PATH):
    os.remove(JSON_FILE_PATH)

# Initialize an empty list to store telemetry data
telemetry_data = []

# Track which packet IDs have already been printed
printed_packets = set()

def parse_telemetry_data(data):
    # Check if the received data is large enough
    if len(data) < 24:  # Minimum size for the header
        print("Received data is too small to contain a valid packet.")
        return

    # Unpack the packet header
    header_format = '>HBBBBQfIBB'  # Format for PacketHeader
    header_size = struct.calcsize(header_format)
    header_data = struct.unpack_from(header_format, data, 0)

    # Extract header information
    packet_id = header_data[4]
    packet_names = {
        0: "Motion data",
        1: "Session data",
        2: "Lap data",
        3: "Event data",
        4: "Participants data",
        5: "Car setups data",
        6: "Car telemetry data",
        7: "Car status data",
        8: "Final classification data",
        9: "Lobby info data",
        10: "Car damage data",
        11: "Session history data"
    }
    packet_name = packet_names.get(packet_id, "Unknown")

    # Add summary info and raw data to telemetry_data for easier inspection
    telemetry_data.append({
        'Packet ID': packet_id,
        'Packet Name': packet_name,
        'Data Size': len(data),
        'Raw Data': list(data)  # Store the raw bytes as a list of integers for readability
    })

    print(f"Received packet ID: {packet_id}, Size: {len(data)} bytes")

    if packet_id not in printed_packets:
        if packet_id == 0:  # Motion data
            print(f"Packet 0 (Motion data) received. Data size: {len(data)} bytes.")
            # Unpack motion data here (not shown for brevity)

        elif packet_id == 1:  # Session data
            print(f"Packet 1 (Session data) received. Data size: {len(data)} bytes.")
            # Unpack session data here (not shown for brevity)

        elif packet_id == 2:  # Lap data
            print(f"Packet 2 (Lap data) received. Data size: {len(data)} bytes.")
            # Unpack lap data here (not shown for brevity)

        elif packet_id == 3:  # Event data
            print(f"Packet 3 (Event data) received. Data size: {len(data)} bytes.")
            # Unpack event data here (not shown for brevity)

        elif packet_id == 4:  # Participants data
            print(f"Packet 4 (Participants data) received. Data size: {len(data)} bytes.")
            # Unpack participants data here (not shown for brevity)

        elif packet_id == 5:  # Car setups data
            print(f"Packet 5 (Car setups data) received. Data size: {len(data)} bytes.")
            # Unpack car setups data here (not shown for brevity)

        elif packet_id == 6:  # Car telemetry data
            print(f"Packet 6 (Car telemetry data) received. Data size: {len(data)} bytes.")
            # All previous code for car telemetry data is commented out for debugging

        elif packet_id == 7:  # Car status data
            print(f"Packet 7 (Car status data) received. Data size: {len(data)} bytes.")
            # Unpack car status data here (not shown for brevity)

        elif packet_id == 8:  # Final classification data
            print(f"Packet 8 (Final classification data) received. Data size: {len(data)} bytes.")
            # Unpack final classification data here (not shown for brevity)

        elif packet_id == 9:  # Lobby info data
            print(f"Packet 9 (Lobby info data) received. Data size: {len(data)} bytes.")
            # Unpack lobby info data here (not shown for brevity)

        elif packet_id == 10:  # Car damage data
            print(f"Packet 10 (Car damage data) received. Data size: {len(data)} bytes.")
            # Unpack car damage data here (not shown for brevity)

        elif packet_id == 11:  # Session history data
            print(f"Packet 11 (Session history data) received. Data size: {len(data)} bytes.")
            # Unpack session history data here (not shown for brevity)

        printed_packets.add(packet_id)

    # Save the telemetry data to a JSON file
    with open(JSON_FILE_PATH, 'w') as json_file:
        json.dump(telemetry_data, json_file, indent=4)  # Write the data with indentation for readability

def start_udp_server():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 20777
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"Listening for telemetry data on {UDP_IP}:{UDP_PORT}...")

    while True:
        data, addr = sock.recvfrom(2048)  # Adjust buffer size as needed
        parse_telemetry_data(data)

if __name__ == "__main__":
    start_udp_server()
