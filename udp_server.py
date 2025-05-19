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

def parse_telemetry_data(data):
    # Unpack the packet header
    header_format = '>HBBBBQfIBB'  # Format for PacketHeader
    header_size = struct.calcsize(header_format)
    header_data = struct.unpack_from(header_format, data, 0)

    # Extract header information
    packet_format = header_data[0]
    game_major_version = header_data[1]
    game_minor_version = header_data[2]
    packet_version = header_data[3]
    packet_id = header_data[4]
    session_uid = header_data[5]
    session_time = header_data[6]
    frame_identifier = header_data[7]
    player_car_index = header_data[8]
    secondary_player_car_index = header_data[9]

    # Unpack the car telemetry data
    car_telemetry_data = []
    telemetry_data_start = header_size  # Start after the header

    for i in range(22):  # There are 22 cars
        offset = telemetry_data_start + i * 1347  # Each car telemetry data is 1347 bytes
        car_data_format = '>HffffBhiBHHHBBBBH4f4B'  # Format for CarTelemetryData
        car_data = struct.unpack_from(car_data_format, data, offset)
        
        car_telemetry = {
            'Speed': car_data[0],  # Speed of car in km/h
            'Throttle': car_data[1],  # Throttle applied (0.0 to 1.0)
            'Steering': car_data[2],  # Steering (-1.0 to 1.0)
            'Brake': car_data[3],  # Brake applied (0.0 to 1.0)
            'Clutch': car_data[4],  # Clutch (0 to 100)
            'Gear': car_data[5],  # Gear selected (1-8, N=0, R=-1)
            #'EngineRPM': car_data[6],  # Engine RPM
            #'DRS': car_data[7],  # DRS (0 = off, 1 = on)
            #'RevLightsPercent': car_data[8],  # Rev lights percentage
            #'RevLightsBitValue': car_data[9],  # Rev lights bit value
            #'BrakesTemperature': car_data[10:14],  # Brakes temperature
            #'TyresSurfaceTemperature': car_data[14:18],  # Tyres surface temperature
            #'TyresInnerTemperature': car_data[18:22],  # Tyres inner temperature
            #'EngineTemperature': car_data[22],  # Engine temperature
            #'TyresPressure': car_data[23:27],  # Tyres pressure
            #'SurfaceType': car_data[27:31]  # Driving surface
        }
        car_telemetry_data.append(car_telemetry)

    # Append the telemetry data to the list
    telemetry_data.append({
        'Packet ID': packet_id,
        'Session UID': session_uid,
        'Session Time': session_time,
        'Player Car Index': player_car_index,
        'Car Telemetry Data': car_telemetry_data
    })

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
        data, addr = sock.recvfrom(4096)  # Buffer size is now 4096 bytes
        parse_telemetry_data(data)

if __name__ == "__main__":
    start_udp_server()
