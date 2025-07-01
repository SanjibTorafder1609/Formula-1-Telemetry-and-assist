import struct
import json
import os
from typing import Dict, Any, List, Optional

# Input and output paths
INPUT_FILE = 'telemetry_logs\Mexico_2025-06-30_19-55-18.bin'
OUTPUT_FILE = 'decoded_telemetry.json'

def read_packets(file_path: str) -> List[bytes]:
    """Read all packets from the binary file."""
    packets = []
    with open(file_path, 'rb') as f:
        while True:
            length_bytes = f.read(2)
            if not length_bytes:
                break
            length = struct.unpack('<H', length_bytes)[0]
            packet = f.read(length)
            if len(packet) != length:
                break  # Incomplete packet
            packets.append(packet)
    return packets

def decode_packet_header(packet: bytes) -> Dict[str, Any]:
    """Decode the common header for all packet types."""
    header_format = '<HBBBBQfIBB'
    header = struct.unpack_from(header_format, packet)
    return {
        'packet_format': header[0],
        'game_major_version': header[1],
        'game_minor_version': header[2],
        'packet_version': header[3],
        'packet_id': header[4],
        'session_uid': header[5],
        'session_time': header[6],
        'frame_identifier': header[7],
        'player_car_index': header[8],
        'secondary_player_car_index': header[9]
    }

def decode_motion(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        header_size = struct.calcsize('<HBBBBQfIBB')
        car_motion_format = '<fff fff hhh hhh fff fff'  # 60 bytes per car
        car_motion_size = struct.calcsize(car_motion_format)

        extra_data_format = '<4f4f4f4f4f3f3f3f f'
        extra_data_size = struct.calcsize(extra_data_format)

        expected_size = header_size + (22 * car_motion_size) + extra_data_size

        if len(packet) != expected_size:
            print(f" Packet length mismatch: got {len(packet)}, expected {expected_size}")

        player_index = header['player_car_index']
        car_offset = header_size + (player_index * car_motion_size)
        car_motion = struct.unpack_from(car_motion_format, packet, car_offset)

        extra_offset = header_size + (22 * car_motion_size)
        extra_data = struct.unpack_from(extra_data_format, packet, extra_offset)

        def normalize(val): return max(-1.0, min(1.0, val / 32767.0))

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'position': dict(zip(('x', 'y', 'z'), car_motion[0:3])),
            'velocity': dict(zip(('x', 'y', 'z'), car_motion[3:6])),
            'forward_dir': dict(zip(('x', 'y', 'z'), map(normalize, car_motion[6:9]))),
            'right_dir': dict(zip(('x', 'y', 'z'), map(normalize, car_motion[9:12]))),
            'g_force': dict(zip(('lateral', 'longitudinal', 'vertical'), car_motion[12:15])),
            'rotation': dict(zip(('yaw', 'pitch', 'roll'), car_motion[15:18])),
            'suspension_position': list(extra_data[0:4]),
            'suspension_velocity': list(extra_data[4:8]),
            'suspension_acceleration': list(extra_data[8:12]),
            'wheel_speed': list(extra_data[12:16]),
            'wheel_slip': list(extra_data[16:20]),
            'local_velocity': dict(zip(('x', 'y', 'z'), extra_data[20:23])),
            'angular_velocity': dict(zip(('x', 'y', 'z'), extra_data[23:26])),
            'angular_acceleration': dict(zip(('x', 'y', 'z'), extra_data[26:29])),
            # If the final float is missing, this won't be included
            'front_wheels_angle': extra_data[29] if len(extra_data) > 29 else None
        }

    except Exception as e:
        print(f" Error decoding motion packet: {e}")
        return None


def decode_session(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        header_size = struct.calcsize('<HBBBBQfIBB')
        session_format = '<BbbBH BbBHHBBBBBB'
        session_size = struct.calcsize(session_format)

        session_data = struct.unpack_from(session_format, packet, header_size)

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'weather': session_data[0],
            'track_temp': session_data[1],
            'air_temp': session_data[2],
            'total_laps': session_data[3],
            'track_length': session_data[4],
            'session_type': session_data[5],
            'track_id': session_data[6],
            'formula': session_data[7],
            'session_time_left': session_data[8],
            'session_duration': session_data[9],
            'pit_speed_limit': session_data[10],
            'game_paused': session_data[11],
            'is_spectating': session_data[12],
            'spectator_car_index': session_data[13],
            'sli_pro_native_support': session_data[14],
            'num_marshal_zones': session_data[15],
             # Assist settings
            'assist_settings': {
                'steering_assist': assist_data[0],
                'braking_assist': assist_data[1],
                'gearbox_assist': assist_data[2],
                'pit_assist': assist_data[3],
                'pit_release_assist': assist_data[4],
                'ers_assist': assist_data[5],
                'drs_assist': assist_data[6],
                'racing_line': assist_data[7],
                'racing_line_type': assist_data[8]
            }
        }

    except Exception as e:
        print(f" Error decoding session packet: {e}")
        return None


def decode_lap_data(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode lap data packet (ID 2)."""
    # TODO: Implement lap data packet decoding
    return None

def decode_event(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode event packet (ID 3)."""
    # TODO: Implement event packet decoding
    return None

def decode_participants(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode participants packet (ID 4)."""
    # TODO: Implement participants packet decoding
    return None

def decode_car_setups(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode car setups packet (ID 5)."""
    # TODO: Implement car setups packet decoding
    return None

def decode_car_telemetry(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    header_size = struct.calcsize('<HBBBBQfIBB')
    car_format = '<HfffBbHBBH4H4B4BH4f4B'
    car_size = struct.calcsize(car_format)
    offset = header_size + (car_size * header['player_car_index'])

    try:
        values = struct.unpack_from(car_format, packet, offset)
    except struct.error:
        return None  # Skip corrupted packet

    return {
        'packet_id': header['packet_id'],
        'frame_id': header['frame_identifier'],
        'speed': values[0],
        'throttle': values[1],
        'steer': values[2],
        'brake': values[3],
        'clutch': values[4],
        'gear': values[5],
        'engine_rpm': values[6],
        'drs': values[7],
        'rev_lights_percent': values[8],
        'rev_lights_bit_value': values[9],
        'brakes_temperature': list(values[10:14]),
        'tyres_surface_temperature': list(values[14:18]),
        'tyres_inner_temperature': list(values[18:22]),
        'engine_temperature': values[22],
        'tyres_pressure': list(values[23:27]),
        'surface_type': list(values[27:31])
    }

def decode_car_status(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode car status packet (ID 7)."""
    # TODO: Implement car status packet decoding
    return None

def decode_final_classification(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode final classification packet (ID 8)."""
    # TODO: Implement final classification packet decoding
    return None

def decode_lobby_info(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode lobby info packet (ID 9)."""
    # TODO: Implement lobby info packet decoding
    return None

def decode_car_damage(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode car damage packet (ID 10)."""
    # TODO: Implement car damage packet decoding
    return None

def decode_session_history(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Decode session history packet (ID 11)."""
    # TODO: Implement session history packet decoding
    return None

def main():
    decoded_data = []
    packets = read_packets(INPUT_FILE)
    first_motion = next(p for p in packets if decode_packet_header(p)['packet_id'] == 0)
    header = decode_packet_header(first_motion)
    print("Motion packet header:", header)

    # Check if player_car_index is valid (should be 0-21)
    print("Player car index:", header['player_car_index'])

    for packet in packets:
        header = decode_packet_header(packet)
        packet_id = header['packet_id']

        if packet_id == 0:  # Motion
            motion = decode_motion(packet, header)
            if motion:
                decoded_data.append(motion)
                
        elif packet_id == 1:  # Session
            session = decode_session(packet, header)
            if session:
                decoded_data.append(session)
                
        elif packet_id == 2:  # Lap Data
            lap_data = decode_lap_data(packet, header)
            if lap_data:
                decoded_data.append(lap_data)
                
        elif packet_id == 3:  # Event
            event = decode_event(packet, header)
            if event:
                decoded_data.append(event)
                
        elif packet_id == 4:  # Participants
            participants = decode_participants(packet, header)
            if participants:
                decoded_data.append(participants)
                
        elif packet_id == 5:  # Car Setups
            car_setups = decode_car_setups(packet, header)
            if car_setups:
                decoded_data.append(car_setups)
                
        elif packet_id == 6:  # Car Telemetry
            telemetry = decode_car_telemetry(packet, header)
            if telemetry:
                decoded_data.append(telemetry)
                
        elif packet_id == 7:  # Car Status
            car_status = decode_car_status(packet, header)
            if car_status:
                decoded_data.append(car_status)
                
        elif packet_id == 8:  # Final Classification
            final_classification = decode_final_classification(packet, header)
            if final_classification:
                decoded_data.append(final_classification)
                
        elif packet_id == 9:  # Lobby Info
            lobby_info = decode_lobby_info(packet, header)
            if lobby_info:
                decoded_data.append(lobby_info)
                
        elif packet_id == 10:  # Car Damage
            car_damage = decode_car_damage(packet, header)
            if car_damage:
                decoded_data.append(car_damage)
                
        elif packet_id == 11:  # Session History
            session_history = decode_session_history(packet, header)
            if session_history:
                decoded_data.append(session_history)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(decoded_data, f, indent=2)

    print(f"Decoding to {OUTPUT_FILE} complete")

if __name__ == "__main__":
    main()