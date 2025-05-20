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
    if len(data) < 24:
        print("Received data is too small to contain a valid packet.")
        return

    # PacketHeader: Little Endian
    header_format = '<HBBBBQfIBB'
    header_size = struct.calcsize(header_format)
    header = struct.unpack_from(header_format, data, 0)

    packet_id = header[4]
    player_index = header[8]
    print(f"Packet ID: {packet_id}, Size: {len(data)}")

    if packet_id not in printed_packets:
        print(f"First time receiving packet ID {packet_id}.")
        printed_packets.add(packet_id)

    # if packet_id == 2:  # Lap Data Packet
    #     lap_format = '<IIHHfffBBBBBBBBBBBBBBHHB'
    #     lap_size = struct.calcsize(lap_format)
    #     offset = header_size + (lap_size * player_index)

    #     values = struct.unpack_from(lap_format, data, offset)
    #     lap_data = {
    #         'lastLapTimeInMS': values[0],
    #         'currentLapTimeInMS': values[1],
    #         'sector1TimeInMS': values[2],
    #         'sector2TimeInMS': values[3],
    #         'lapDistance': values[4],
    #         'totalDistance': values[5],
    #         'safetyCarDelta': values[6],
    #         'carPosition': values[7],
    #         'currentLapNum': values[8],
    #         'pitStatus': values[9],
    #         'numPitStops': values[10],
    #         'sector': values[11],
    #         'currentLapInvalid': values[12],
    #         'penalties': values[13],
    #         'warnings': values[14],
    #         'numUnservedDriveThroughPens': values[15],
    #         'numUnservedStopGoPens': values[16],
    #         'gridPosition': values[17],
    #         'driverStatus': values[18],
    #         'resultStatus': values[19],
    #         'pitLaneTimerActive': values[20],
    #         'pitLaneTimeInLaneInMS': values[21],
    #         'pitStopTimerInMS': values[22],
    #         'pitStopShouldServePen': values[23]
    #     }

    #     print("Player lap data:")
    #     print(json.dumps(lap_data, indent=2))

    #     telemetry_data.append({
    #         'header': {
    #             'packetId': packet_id,
    #             'frameIdentifier': header[7],
    #             'playerCarIndex': player_index
    #         },
    #         'lapData': lap_data
    #     })

    elif packet_id == 6:  # Car Telemetry Packet
        car_format = '<HfffBbHBBH4H4B4BH4f4B'
        car_size = struct.calcsize(car_format)
        offset = header_size + (car_size * player_index)

        values = struct.unpack_from(car_format, data, offset)
        car_data = {
            'speed': values[0],
            'throttle': values[1],
            'steer': values[2],
            'brake': values[3],
            'clutch': values[4],
            'gear': values[5],
            'engineRPM': values[6],
            'drs': values[7],
            'revLightsPercent': values[8],
            'revLightsBitValue': values[9],
            'brakesTemperature': list(values[10:14]),
            'tyresSurfaceTemperature': list(values[14:18]),
            'tyresInnerTemperature': list(values[18:22]),
            'engineTemperature': values[22],
            'tyresPressure': list(values[23:27]),
            'surfaceType': list(values[27:31])
        }

        # After car data array of 22 cars, read the footer
        footer_offset = header_size + (car_size * 22)
        mfd_panel_index, mfd_panel_secondary, suggested_gear = struct.unpack_from('<BBb', data, footer_offset)

        print(f"Suggested Gear: {suggested_gear}")
        print("Player car telemetry:")
        print(json.dumps(car_data, indent=2))

        telemetry_data.append({
            'header': {
                'packetId': packet_id,
                'frameIdentifier': header[7],
                'playerCarIndex': player_index
            },
            'carTelemetryData': car_data,
            'mfdPanelIndex': mfd_panel_index,
            'mfdPanelIndexSecondary': mfd_panel_secondary,
            'suggestedGear': suggested_gear
        })

    # Save to file (append data)
    with open(JSON_FILE_PATH, 'w') as json_file:
        json.dump(telemetry_data, json_file, indent=2)

def start_udp_server():
    UDP_IP = "127.0.0.1"
    UDP_PORT = 20777
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))

    print(f"Listening for telemetry data on {UDP_IP}:{UDP_PORT}...")

    while True:
        data, addr = sock.recvfrom(2048)
        parse_telemetry_data(data)

if __name__ == "__main__":
    start_udp_server()
