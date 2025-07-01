import socket
import struct
import os
from datetime import datetime

# Folder to store logs
LOG_FOLDER = "telemetry_logs"

# Mapping from trackId to track name
TRACK_NAMES = {
    0: "Melbourne", 1: "Paul_Ricard", 2: "Shanghai", 3: "Sakhir",
    4: "Catalunya", 5: "Monaco", 6: "Montreal", 7: "Silverstone",
    8: "Hockenheim", 9: "Hungaroring", 10: "Spa", 11: "Monza",
    12: "Singapore", 13: "Suzuka", 14: "Abu_Dhabi", 15: "Texas",
    16: "Brazil", 17: "Austria", 18: "Sochi", 19: "Mexico",
    20: "Baku", 21: "Sakhir_Short", 22: "Silverstone_Short",
    23: "Texas_Short", 24: "Suzuka_Short", 25: "Hanoi",
    26: "Zandvoort", 27: "Imola", 28: "Portimao", 29: "Jeddah"
}

def dump_session_packet(packet):
    header_format = '<HBBBBQfIBB'
    header_size = struct.calcsize(header_format)
    offset = header_size

    session_format = '<BbbB H B b B H H B B B B B B'
    session_size = struct.calcsize(session_format)

    if len(packet) < offset + session_size:
        print("Session packet too short.")
        return None

    fields = struct.unpack_from(session_format, packet, offset)

    print(f"Track Name: {TRACK_NAMES.get(fields[6], 'Unknown')}")

    return fields[6]


def start_packet_logger():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 20777

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print(f" Listening for telemetry on {UDP_IP}:{UDP_PORT}...")

    # Ensure folder exists
    os.makedirs(LOG_FOLDER, exist_ok=True)

    track_name = None
    file = None

    while True:
        data, _ = sock.recvfrom(2048)

        if not track_name:
            header_format = '<HBBBBQfIBB'
            packet_id = struct.unpack_from(header_format, data)[4]

            if packet_id == 1:
                track_id = dump_session_packet(data)
                if track_id is not None:
                    track_name = TRACK_NAMES.get(track_id, f"UnknownTrack_{track_id}")
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    filename = f"{track_name}_{timestamp}.bin"
                    file_path = os.path.join(LOG_FOLDER, filename)
                    file = open(file_path, 'ab')
                    print(f"\n Logging to: {file_path}")

        if file:
            file.write(struct.pack('<H', len(data)))
            file.write(data)

if __name__ == "__main__":
    start_packet_logger()
