"""
test_uart.py
Run this BEFORE main.py to verify all three UART ports are working.

Usage: python3 test_uart.py
"""

import sys
import time

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed.")
    print("Run: sudo apt install python3-serial")
    sys.exit(1)

PORTS = {
    "Sensor_1 (UART0)": "/dev/ttyAMA0",
    "Sensor_2 (UART3)": "/dev/ttyAMA3",
    "Sensor_3 (UART4)": "/dev/ttyAMA4",
}
BAUD  = 256000
SECS  = 3   # seconds to listen per port

print("=" * 50)
print("  LD2410S UART Test")
print("=" * 50)

all_ok = True

for name, port in PORTS.items():
    print(f"\n[Test] {name} on {port}")
    try:
        with serial.Serial(port, BAUD, timeout=0.5) as ser:
            print(f"  ✔ Port opened successfully")
            print(f"  Listening for {SECS}s...")
            deadline = time.time() + SECS
            byte_count = 0
            while time.time() < deadline:
                chunk = ser.read(64)
                byte_count += len(chunk)
            if byte_count > 0:
                print(f"  ✔ Received {byte_count} bytes — sensor is transmitting")
            else:
                print(f"  ⚠ No data received — check wiring (TX/RX crossed?)")
                all_ok = False
    except serial.SerialException as e:
        print(f"  ✗ FAILED: {e}")
        all_ok = False

print("\n" + "=" * 50)
if all_ok:
    print("  All UARTs OK — run python3 src/main.py")
else:
    print("  Some UARTs failed — check docs/troubleshooting.md")
print("=" * 50)
