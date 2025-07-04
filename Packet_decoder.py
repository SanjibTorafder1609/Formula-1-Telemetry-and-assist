import struct
import json
import os
import time
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Input and output paths
INPUT_FILE = 'telemetry_logs\Mexico_2025-07-01_13-52-58.bin'
OUTPUT_FILE = 'decoded_telemetry.json'

HEADER_FORMAT = '<HBBBBQfIBB'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
NUM_CARS = 22

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
    header = struct.unpack_from(HEADER_FORMAT, packet)
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
# packet 0
def decode_motion(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        car_motion_format = '<fff fff hhh hhh fff fff'  # 60 bytes per car
        car_motion_size = struct.calcsize(car_motion_format)

        extra_data_format = '<4f4f4f4f4f3f3f3f f'
        extra_data_size = struct.calcsize(extra_data_format)

        expected_size = HEADER_SIZE + (22 * car_motion_size) + extra_data_size

        if len(packet) != expected_size:
            print(f" Packet length mismatch: got {len(packet)}, expected {expected_size}")

        player_index = header['player_car_index']
        car_offset = HEADER_SIZE + (player_index * car_motion_size)
        car_motion = struct.unpack_from(car_motion_format, packet, car_offset)

        extra_offset = HEADER_SIZE + (22 * car_motion_size)
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
            'front_wheels_angle': extra_data[29] if len(extra_data) > 29 else None
        }

    except Exception as e:
        print(f" Error decoding motion packet: {e}")
        return None

# packet 1
def decode_session(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        # 22 cars, each with 9 bytes of data
        session_format = '<BbbBH BbBHHBBBBBB'
        session_data = struct.unpack_from(session_format, packet, HEADER_SIZE)
        
        # Assist settings — 9 bytes at the very end
        assist_format = '<BBBBBBBBB'
        assist_data = struct.unpack_from(assist_format, packet, len(packet) - 9)

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
# packet 2
def decode_lap_data(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        lap_data_format = '<IIHHfffBBBBBBBBBBBBBBHHB'
        lap_data_size = struct.calcsize(lap_data_format)

        player_index = header['player_car_index']
        offset = HEADER_SIZE + (lap_data_size * player_index)

        lap_values = struct.unpack_from(lap_data_format, packet, offset)

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'last_lap_time_ms': lap_values[0],
            'current_lap_time_ms': lap_values[1],
            'sector1_time_ms': lap_values[2],
            'sector2_time_ms': lap_values[3],
            'lap_distance': lap_values[4],
            'total_distance': lap_values[5],
            'safety_car_delta': lap_values[6],
            'car_position': lap_values[7],
            'current_lap_num': lap_values[8],
            'pit_status': lap_values[9],
            'num_pit_stops': lap_values[10],
            'sector': lap_values[11],
            'current_lap_invalid': lap_values[12],
            'penalties': lap_values[13],
            'warnings': lap_values[14],
            'num_unserved_drive_through_pens': lap_values[15],
            'num_unserved_stop_go_pens': lap_values[16],
            'grid_position': lap_values[17],
            'driver_status': lap_values[18],
            'result_status': lap_values[19],
            'pit_lane_timer_active': lap_values[20],
            'pit_lane_time_in_lane_ms': lap_values[21],
            'pit_stop_timer_ms': lap_values[22],
            'pit_stop_should_serve_pen': lap_values[23]
        }

    except Exception as e:
        print(f" Error decoding lap data packet: {e}")
        return None
# packet 3
def decode_event(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        event_offset = HEADER_SIZE
        event_code = struct.unpack_from('<4s', packet, event_offset)[0].decode('utf-8')

        event_data = {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'event_code': event_code
        }

        # Optional: decode event-specific data
        if event_code == 'FTLP': # Fastest Lap
            vehicle_idx, lap_time = struct.unpack_from('<Bf', packet, event_offset + 4)
            event_data['vehicle_idx'] = vehicle_idx
            event_data['lap_time'] = lap_time

        elif event_code == 'RTMT': # Retirement
            vehicle_idx = struct.unpack_from('<B', packet, event_offset + 4)[0]
            event_data['vehicle_idx'] = vehicle_idx

        elif event_code == 'RCWN': # Race Winner
            vehicle_idx = struct.unpack_from('<B', packet, event_offset + 4)[0]
            event_data['winner'] = vehicle_idx

        elif event_code == 'PENA': # Penalty
            pena_format = '<BBBBBHB'
            values = struct.unpack_from(pena_format, packet, event_offset + 4)
            event_data.update({
                'penalty_type': values[0],
                'infringement_type': values[1],
                'vehicle_idx': values[2],
                'other_vehicle_idx': values[3],
                'time': values[4],
                'lap_num': values[5],
                'places_gained': values[6]
            })

        elif event_code == 'SPTP': # Speed Trap - Fastest Speed
            sptp_format = '<BfB'
            values = struct.unpack_from(sptp_format, packet, event_offset + 4)
            event_data.update({
                'vehicle_idx': values[0],
                'speed': values[1],
                'is_overall_fastest': values[2]
            })

        return event_data

    except Exception as e:
        print(f" Error decoding event packet: {e}")
        return None

# packet 4
def decode_participants(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        offset = HEADER_SIZE

        num_active_cars = struct.unpack_from('<B', packet, offset)[0]
        offset += 1

        participant_format = '<BBBBBBB48sB'
        participant_size = struct.calcsize(participant_format)

        participants = []
        for i in range(NUM_CARS):  # Usually 22
            data = struct.unpack_from(participant_format, packet, offset + i * participant_size)
            name = data[7].decode('utf-8', errors='ignore').rstrip('\x00')

            participants.append({
                'index': i,
                'ai_controlled': bool(data[0]),
                'driver_id': data[1],
                'network_id': data[2],
                'team_id': data[3],
                'my_team': bool(data[4]),
                'race_number': data[5],
                'nationality': data[6],
                'name': name,
                'telemetry_public': bool(data[8])
            })

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'num_active_cars': num_active_cars,
            'participants': participants
        }

    except Exception as e:
        print(f" Error decoding participants packet: {e}")
        return None

# packet 5
def decode_car_setups(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        offset = HEADER_SIZE
        setup_format = '<BBBBffffBBBBBBBBffffBf'
        setup_size = struct.calcsize(setup_format)

        car_setups = []
        for i in range(NUM_CARS):  # Usually 22
            values = struct.unpack_from(setup_format, packet, offset + i * setup_size)
            car_setups.append({
                'index': i,
                'front_wing': values[0],
                'rear_wing': values[1],
                'on_throttle': values[2],
                'off_throttle': values[3],
                'front_camber': values[4],
                'rear_camber': values[5],
                'front_toe': values[6],
                'rear_toe': values[7],
                'front_suspension': values[8],
                'rear_suspension': values[9],
                'front_anti_roll_bar': values[10],
                'rear_anti_roll_bar': values[11],
                'front_suspension_height': values[12],
                'rear_suspension_height': values[13],
                'brake_pressure': values[14],
                'brake_bias': values[15],
                'rear_left_tyre_pressure': values[16],
                'rear_right_tyre_pressure': values[17],
                'front_left_tyre_pressure': values[18],
                'front_right_tyre_pressure': values[19],
                'ballast': values[20],
                'fuel_load': values[21]
            })

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'car_setups': car_setups
        }

    except Exception as e:
        print(f" Error decoding car setups packet: {e}")
        return None

# packet 6
def decode_car_telemetry(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    car_format = '<HfffBbHBBH4H4B4BH4f4B'
    car_size = struct.calcsize(car_format)
    player_index = header['player_car_index']
    car_offset = HEADER_SIZE + (car_size * player_index)

    try:
        values = struct.unpack_from(car_format, packet, car_offset)

        # Footer offset = after all 22 cars
        footer_offset = HEADER_SIZE + (car_size * NUM_CARS)
        mfd_panel_index, mfd_panel_secondary, suggested_gear = struct.unpack_from('<BBb', packet, footer_offset)

    except struct.error:
        return None

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
        'surface_type': list(values[27:31]),

        # Footer
        'mfd_panel_index': mfd_panel_index,
        'mfd_panel_index_secondary': mfd_panel_secondary,
        'suggested_gear': suggested_gear
    }

# packet 7
def decode_car_status(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        offset = HEADER_SIZE
        car_format = '<5B 3f 2H 2B H 3B b f B 3f B'
        car_size = struct.calcsize(car_format)

        player_index = header['player_car_index']
        car_offset = offset + (car_size * player_index)
        values = struct.unpack_from(car_format, packet, car_offset)

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'traction_control': values[0],
            'abs': values[1],
            'fuel_mix': values[2],
            'brake_bias': values[3],
            'pit_limiter_status': values[4],
            'fuel_in_tank': values[5],
            'fuel_capacity': values[6],
            'fuel_remaining_laps': values[7],
            'max_rpm': values[8],
            'idle_rpm': values[9],
            'max_gears': values[10],
            'drs_allowed': values[11],
            'drs_activation_distance': values[12],
            'actual_tyre_compound': values[13],
            'visual_tyre_compound': values[14],
            'tyres_age_laps': values[15],
            'vehicle_fia_flags': values[16],
            'ers_store_energy': values[17],
            'ers_deploy_mode': values[18],
            'ers_harvested_mguk': values[19],
            'ers_harvested_mguh': values[20],
            'ers_deployed': values[21],
            'network_paused': values[22]
        }

    except Exception as e:
        print(f" Error decoding car status packet: {e}")
        return None

# packet 8
def decode_final_classification(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        offset = HEADER_SIZE
        NUM_CARS = struct.unpack_from('<B', packet, offset)[0]
        offset += 1

        classification_format = '<6B I d 3B 8B 8B 8B'
        classification_size = struct.calcsize(classification_format)

        player_index = header['player_car_index']
        player_offset = offset + player_index * classification_size
        values = struct.unpack_from(classification_format, packet, player_offset)

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'position': values[0],
            'num_laps': values[1],
            'grid_position': values[2],
            'points': values[3],
            'num_pit_stops': values[4],
            'result_status': values[5],
            'best_lap_time_ms': values[6],
            'total_race_time': values[7],
            'penalties_time': values[8],
            'num_penalties': values[9],
            'num_tyre_stints': values[10],
            'tyre_stints_actual': list(values[11:19]),
            'tyre_stints_visual': list(values[19:27]),
            'tyre_stints_end_laps': list(values[27:35])
        }

    except Exception as e:
        print(f" Error decoding final classification packet: {e}")
        return None

#not working on this since i rarely ever play online multiplayer, yes i play alone, shut up
# packet 9
def decode_lobby_info(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    return None

# packet 10
def decode_car_damage(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        car_format = '<4f4B4B15B'
        car_size = struct.calcsize(car_format)

        player_index = header['player_car_index']
        player_offset = HEADER_SIZE + (car_size * player_index)

        if len(packet) < player_offset + car_size:
            print(f" Packet too short for car damage (have {len(packet)}, need {player_offset + car_size})")
            return None

        values = struct.unpack_from(car_format, packet, player_offset)

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'tyres_wear': list(values[0:4]),
            'tyres_damage': list(values[4:8]),
            'brakes_damage': list(values[8:12]),
            'front_left_wing_damage': values[12],
            'front_right_wing_damage': values[13],
            'rear_wing_damage': values[14],
            'floor_damage': values[15],
            'diffuser_damage': values[16],
            'sidepod_damage': values[17],
            'drs_fault': values[18],
            'gearbox_damage': values[19],
            'engine_damage': values[20],
            'engine_mguh_wear': values[21],
            'engine_es_wear': values[22],
            'engine_ce_wear': values[23],
            'engine_ice_wear': values[24],
            'engine_mguk_wear': values[25],
            'engine_tc_wear': values[26]
        }

    except Exception as e:
        print(f" Error decoding car from here damage packet: {e}")
        return None

# packet 11
def decode_session_history(packet: bytes, header: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        offset = HEADER_SIZE

        car_idx, num_laps, num_stints, best_lap, best_s1, best_s2, best_s3 = struct.unpack_from('<7B', packet, offset)
        offset += 7

        lap_history_format = '<IHHHB'
        lap_size = struct.calcsize(lap_history_format)

        lap_history = []
        for i in range(100):
            lap_offset = offset + i * lap_size
            if lap_offset + lap_size > len(packet):
                break
            lap_data = struct.unpack_from(lap_history_format, packet, lap_offset)
            lap_history.append({
                'lap_time_ms': lap_data[0],
                'sector1_time_ms': lap_data[1],
                'sector2_time_ms': lap_data[2],
                'sector3_time_ms': lap_data[3],
                'lap_valid_flags': {
                    'lap_valid': bool(lap_data[4] & 0x01),
                    'sector1_valid': bool(lap_data[4] & 0x02),
                    'sector2_valid': bool(lap_data[4] & 0x04),
                    'sector3_valid': bool(lap_data[4] & 0x08),
                }
            })

        offset += 100 * lap_size

        tyre_stints = []
        if len(packet) >= offset + (3 * 8):  # 3 bytes × 8 entries
            for i in range(8):
                stint_offset = offset + i * 3
                stint = struct.unpack_from('<BBB', packet, stint_offset)
                tyre_stints.append({
                    'end_lap': stint[0],
                    'tyre_actual_compound': stint[1],
                    'tyre_visual_compound': stint[2]
                })

        return {
            'packet_id': header['packet_id'],
            'frame_id': header['frame_identifier'],
            'car_index': car_idx,
            'num_laps': num_laps,
            'num_tyre_stints': num_stints,
            'best_lap_lap_num': best_lap,
            'best_sector1_lap_num': best_s1,
            'best_sector2_lap_num': best_s2,
            'best_sector3_lap_num': best_s3,
            'lap_history': lap_history[:num_laps],
            'tyre_stints': tyre_stints[:num_stints]
        }

    except Exception as e:
        print(f" Error decoding session history packet: {e}")
        return None


PACKET_DECODERS = {
    0: decode_motion,
    1: decode_session,
    2: decode_lap_data,
    3: decode_event,
    4: decode_participants,
    5: decode_car_setups,
    6: decode_car_telemetry,
    7: decode_car_status,
    8: decode_final_classification,
    9: decode_lobby_info,
    10: decode_car_damage,
    11: decode_session_history,
}

def main():
    packets = read_packets(INPUT_FILE)
    print(f"Processing {len(packets)} packets...")

    frames = defaultdict(dict)
    start_time = time.time()

    for packet in packets:
        header = decode_packet_header(packet)
        packet_id = header['packet_id']
        frame_id = header['frame_identifier']

        decoder = PACKET_DECODERS.get(packet_id)
        if decoder:
            decoded = decoder(packet, header)
            if decoded:
                # Store under the frame_id → packet_type name (optional fallback to 'packet_{id}')
                packet_name = decoder.__name__.replace("decode_", "")
                frames[frame_id][packet_name] = decoded

    end_time = time.time()
    print(f"Decoded data for {len(frames)} frame_ids in {end_time - start_time:.2f} seconds")

    # Optional: sort by frame_id for consistent output
    sorted_frames = dict(sorted(frames.items()))

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(sorted_frames, f, indent=2)

    print(f" Decoding complete → saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()