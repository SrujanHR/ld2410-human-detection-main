"""
sensor_parser.py
Parses LD2410S binary output frames WITHOUT any external libraries.

LD2410S Reporting Frame Format (Basic Reporting mode):
─────────────────────────────────────────────────────
Header:  0xF4 0xF3 0xF2 0xF1       (4 bytes)
Length:  2 bytes little-endian      (payload length)
Payload: variable
Footer:  0xF8 0xF7 0xF6 0xF5       (4 bytes)

Basic Reporting Payload (type 0x02, data type 0x02):
  Byte 0:   0x0D (frame type = reporting)
  Byte 1:   Data type (0x02 = engineering, 0x01 = basic)
  Byte 2:   Target state
               0x00 = no target
               0x01 = moving target
               0x02 = stationary target
               0x03 = moving + stationary
  Byte 3-4: Moving target distance  (uint16, little-endian, cm)
  Byte 5:   Moving target energy    (0–100)
  Byte 6-7: Stationary target distance (uint16, little-endian, cm)
  Byte 8:   Stationary target energy   (0–100)
  Byte 9-10: Detection distance     (uint16, little-endian, cm)

Reference: LD2410S Serial Communication Protocol v1.07
"""

from dataclasses import dataclass, field
import struct
import time


# ─────────────────────────────────────────────
#  DATA CLASS
# ─────────────────────────────────────────────
@dataclass
class SensorData:
    name:              str   = ""
    presence:          bool  = False
    distance_cm:       int   = 0      # detection gate distance
    moving_distance:   int   = 0      # moving target distance (cm)
    moving_energy:     int   = 0      # 0-100
    static_distance:   int   = 0      # stationary target distance (cm)
    static_energy:     int   = 0      # 0-100
    target_state:      int   = 0      # raw state byte
    last_update:       float = field(default_factory=time.time)
    frame_errors:      int   = 0      # cumulative parse errors

    def to_dict(self) -> dict:
        return {
            "presence":        self.presence,
            "distance_cm":     self.distance_cm,
            "moving_distance": self.moving_distance,
            "moving_energy":   self.moving_energy,
            "static_distance": self.static_distance,
            "static_energy":   self.static_energy,
            "target_state":    self.target_state,
            "last_update":     self.last_update,
            "frame_errors":    self.frame_errors,
        }


# ─────────────────────────────────────────────
#  FRAME CONSTANTS
# ─────────────────────────────────────────────
FRAME_HEADER = bytes([0xF4, 0xF3, 0xF2, 0xF1])
FRAME_FOOTER = bytes([0xF8, 0xF7, 0xF6, 0xF5])
HEADER_LEN   = 4
FOOTER_LEN   = 4
LENGTH_FIELD = 2   # bytes after header
MIN_FRAME    = HEADER_LEN + LENGTH_FIELD + 1 + FOOTER_LEN  # absolute minimum


# ─────────────────────────────────────────────
#  PARSER
# ─────────────────────────────────────────────
def parse_ld2410_frame(
    buffer: bytearray,
    sensor_data: SensorData | None = None
) -> tuple[SensorData | None, bytearray]:
    """
    Scan buffer for a complete LD2410 frame.

    Returns:
        (SensorData | None, remaining_buffer)
        SensorData is None if no complete valid frame found.
    """
    result = sensor_data  # may be None

    while True:
        # Find header
        idx = buffer.find(FRAME_HEADER)
        if idx == -1:
            # No header found — keep last 3 bytes (partial header possible)
            buffer = buffer[-3:] if len(buffer) >= 3 else buffer
            return result, buffer

        # Discard bytes before header
        if idx > 0:
            buffer = buffer[idx:]

        # Need at least header + length bytes
        if len(buffer) < HEADER_LEN + LENGTH_FIELD:
            return result, buffer

        # Read payload length
        payload_len = struct.unpack_from("<H", buffer, HEADER_LEN)[0]

        # Total expected frame size
        total_len = HEADER_LEN + LENGTH_FIELD + payload_len + FOOTER_LEN

        # Wait for full frame
        if len(buffer) < total_len:
            return result, buffer

        # Check footer
        footer_start = HEADER_LEN + LENGTH_FIELD + payload_len
        if buffer[footer_start:footer_start + FOOTER_LEN] != FRAME_FOOTER:
            # Bad frame — skip past this header and try again
            buffer = buffer[HEADER_LEN:]
            if sensor_data:
                sensor_data.frame_errors += 1
            continue

        # Extract payload
        payload = buffer[HEADER_LEN + LENGTH_FIELD: footer_start]

        # Consume frame from buffer
        buffer = buffer[total_len:]

        # Parse payload
        parsed = _parse_payload(payload)
        if parsed is not None:
            if sensor_data:
                parsed.name         = sensor_data.name
                parsed.frame_errors = sensor_data.frame_errors
            result = parsed

        # Continue scanning for more frames
        if len(buffer) < MIN_FRAME:
            break

    return result, buffer


def _parse_payload(payload: bytes) -> SensorData | None:
    """
    Decode the payload bytes into a SensorData object.
    Returns None if the payload is too short or unrecognised.
    """
    # Minimum: type(1) + data_type(1) + state(1) + moving_dist(2) +
    #          moving_energy(1) + static_dist(2) + static_energy(1) +
    #          detect_dist(2) = 11 bytes
    if len(payload) < 11:
        return None

    frame_type = payload[0]
    if frame_type != 0x0D:
        # Not a reporting frame (could be ACK or engineering data)
        return None

    # data_type = payload[1]  # 0x01=basic, 0x02=engineering (ignore for now)
    target_state    = payload[2]
    moving_dist     = struct.unpack_from("<H", payload, 3)[0]
    moving_energy   = payload[5]
    static_dist     = struct.unpack_from("<H", payload, 6)[0]
    static_energy   = payload[8]
    detect_dist     = struct.unpack_from("<H", payload, 9)[0]

    presence = target_state != 0x00

    # Pick the best distance to report
    if presence:
        # Prefer the closer of moving/static if both detected
        if target_state == 0x03:
            distance_cm = min(moving_dist, static_dist)
        elif target_state == 0x01:
            distance_cm = moving_dist
        else:
            distance_cm = static_dist
    else:
        distance_cm = detect_dist  # detection gate boundary

    return SensorData(
        presence        = presence,
        distance_cm     = distance_cm,
        moving_distance = moving_dist,
        moving_energy   = moving_energy,
        static_distance = static_dist,
        static_energy   = static_energy,
        target_state    = target_state,
        last_update     = time.time(),
    )


# ─────────────────────────────────────────────
#  SELF-TEST  (run: python3 sensor_parser.py)
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Craft a minimal valid frame: moving target at 120 cm, energy 80
    header  = bytes([0xF4, 0xF3, 0xF2, 0xF1])
    footer  = bytes([0xF8, 0xF7, 0xF6, 0xF5])
    # payload: type=0x0D, data_type=0x01, state=0x01(moving),
    #          moving_dist=120(0x78,0x00), energy=80,
    #          static_dist=0, static_energy=0, detect_dist=120
    payload = bytes([
        0x0D, 0x01, 0x01,
        0x78, 0x00,   # moving_dist = 120 cm
        0x50,         # moving_energy = 80
        0x00, 0x00,   # static_dist = 0
        0x00,         # static_energy = 0
        0x78, 0x00,   # detect_dist = 120
    ])
    length  = struct.pack("<H", len(payload))
    frame   = bytearray(header + length + payload + footer)

    result, remaining = parse_ld2410_frame(frame)
    assert result is not None, "Parse failed!"
    assert result.presence is True
    assert result.distance_cm == 120
    assert result.moving_energy == 80
    print("✓ Self-test passed")
    print(f"  presence      = {result.presence}")
    print(f"  distance_cm   = {result.distance_cm}")
    print(f"  moving_energy = {result.moving_energy}")
