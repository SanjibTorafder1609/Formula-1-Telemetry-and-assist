from collections import Counter
import struct

HEADER_FORMAT = '<HBBBBQfIBB'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
counter = Counter()

with open('telemetry_logs\Mexico_2025-07-01_13-52-58.bin', 'rb') as f:
    while True:
        length_bytes = f.read(2)
        if not length_bytes:
            break
        length = struct.unpack('<H', length_bytes)[0]
        packet = f.read(length)
        if len(packet) != length:
            break
        packet_id = struct.unpack_from(HEADER_FORMAT, packet)[4]
        counter[packet_id] += 1

print(counter)
