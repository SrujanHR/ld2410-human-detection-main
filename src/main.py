"""
Multi-Sensor Human Detection System
Using 3x LD2410S mmWave Radar Sensors + Raspberry Pi 4B

UART Mapping:
  Sensor 1 → /dev/ttyAMA0   (GPIO14=TX, GPIO15=RX)
  Sensor 2 → /dev/ttyAMA3   (GPIO4=TX,  GPIO5=RX)
  Sensor 3 → /dev/ttyAMA4   (GPIO12=TX, GPIO13=RX)

Run: python3 src/main.py
"""

import threading
import time
import signal
import sys
from uart_reader import UARTReader
from sensor_parser import parse_ld2410_frame, SensorData
from web_server import start_web_server

# ─────────────────────────────────────────────
#  CONFIGURATION
# ─────────────────────────────────────────────
SENSORS = {
    "Sensor_1": "/dev/ttyAMA0",
    "Sensor_2": "/dev/ttyAMA3",
    "Sensor_3": "/dev/ttyAMA4",
}
BAUD_RATE      = 256000   # LD2410S default baud rate
OUTPUT_FILE    = "output.json"
WEB_PORT       = 8000

# Shared state — written by reader threads, read by web server / main
sensor_state: dict[str, SensorData] = {
    name: SensorData(name=name) for name in SENSORS
}
state_lock = threading.Lock()

# ─────────────────────────────────────────────
#  SENSOR READER THREAD
# ─────────────────────────────────────────────
def sensor_thread(name: str, port: str):
    """Continuously reads one LD2410S sensor and updates shared state."""
    reader = UARTReader(name=name, port=port, baud=BAUD_RATE)
    buffer = bytearray()

    while True:
        try:
            chunk = reader.read_bytes(64)
            if chunk:
                buffer.extend(chunk)
                # Parse all complete frames from buffer
                parsed, buffer = parse_ld2410_frame(buffer)
                if parsed:
                    with state_lock:
                        sensor_state[name] = parsed
                        sensor_state[name].name = name
        except Exception as e:
            print(f"[{name}] Error: {e} — retrying in 2s")
            reader.reconnect()
            time.sleep(2)

# ─────────────────────────────────────────────
#  DIRECTION / ZONE ESTIMATION
# ─────────────────────────────────────────────
def estimate_direction(state: dict) -> str:
    """
    Rough direction based on which sensors detect motion and at what distance.

    Physical layout assumed:
        Sensor_1 = LEFT
        Sensor_2 = CENTER
        Sensor_3 = RIGHT
    """
    detections = {}
    for name, data in state.items():
        if data.presence and data.distance_cm > 0:
            detections[name] = data.distance_cm

    if not detections:
        return "No Detection"

    # Closest sensor indicates direction
    closest = min(detections, key=detections.get)
    direction_map = {
        "Sensor_1": "LEFT",
        "Sensor_2": "CENTER",
        "Sensor_3": "RIGHT",
    }
    return direction_map.get(closest, "UNKNOWN")

# ─────────────────────────────────────────────
#  MAIN OUTPUT LOOP
# ─────────────────────────────────────────────
def output_loop():
    """Reads shared state, prints to console, writes to output.json."""
    import json
    while True:
        time.sleep(0.5)
        with state_lock:
            snapshot = {k: v.to_dict() for k, v in sensor_state.items()}
            direction = estimate_direction(sensor_state)

        snapshot["direction"] = direction
        snapshot["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")

        # Write JSON for web server
        try:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(snapshot, f, indent=2)
        except OSError as e:
            print(f"[Output] File write error: {e}")

        # Console summary
        print("\033[2J\033[H", end="")  # clear screen
        print("=" * 50)
        print("  Multi-Sensor Human Detection System")
        print("=" * 50)
        for name, data in snapshot.items():
            if isinstance(data, dict):
                present = "✔ DETECTED" if data.get("presence") else "✗ Clear"
                dist    = data.get("distance_cm", 0)
                motion  = data.get("moving_energy", 0)
                static  = data.get("static_energy", 0)
                print(f"  {name:10s} | {present:12s} | {dist:4d} cm | "
                      f"Move:{motion:3d}  Static:{static:3d}")
        print(f"\n  Direction → {direction}")
        print(f"  Web dashboard: http://<PI_IP>:{WEB_PORT}")
        print("=" * 50)

# ─────────────────────────────────────────────
#  GRACEFUL SHUTDOWN
# ─────────────────────────────────────────────
def handle_exit(sig, frame):
    print("\n[Main] Shutting down gracefully…")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("[Main] Starting Multi-Sensor Human Detection System")
    print(f"[Main] Sensors: {list(SENSORS.keys())}")
    print(f"[Main] Baud rate: {BAUD_RATE}")
    print()

    # Start one reader thread per sensor
    for sensor_name, uart_port in SENSORS.items():
        t = threading.Thread(
            target=sensor_thread,
            args=(sensor_name, uart_port),
            daemon=True,
            name=f"Reader-{sensor_name}",
        )
        t.start()
        print(f"[Main] Started thread for {sensor_name} on {uart_port}")

    # Start web server in background thread
    web_thread = threading.Thread(
        target=start_web_server,
        args=(OUTPUT_FILE, WEB_PORT),
        daemon=True,
        name="WebServer",
    )
    web_thread.start()
    print(f"[Main] Web server started on port {WEB_PORT}")

    # Run output loop in main thread (blocks until Ctrl+C)
    output_loop()
