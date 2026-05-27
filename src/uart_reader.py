"""
uart_reader.py
Handles opening, reading, and reconnecting a single UART serial port.
Uses only pyserial (python3-serial via apt).
"""

import serial
import time


class UARTReader:
    """
    Wraps a pyserial Serial object with automatic reconnection.

    Usage:
        reader = UARTReader("Sensor_1", "/dev/ttyAMA0", 256000)
        data = reader.read_bytes(64)
    """

    def __init__(self, name: str, port: str, baud: int, timeout: float = 0.1):
        self.name    = name
        self.port    = port
        self.baud    = baud
        self.timeout = timeout
        self._serial: serial.Serial | None = None
        self._connect()

    # ─────────────────────────────────────────
    #  CONNECTION MANAGEMENT
    # ─────────────────────────────────────────
    def _connect(self):
        """Open serial port. Retries every 3 s until successful."""
        while True:
            try:
                self._serial = serial.Serial(
                    port=self.port,
                    baudrate=self.baud,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=self.timeout,
                )
                print(f"[{self.name}] Connected to {self.port} at {self.baud} baud")
                return
            except serial.SerialException as e:
                print(f"[{self.name}] Cannot open {self.port}: {e} — retrying in 3s")
                time.sleep(3)

    def reconnect(self):
        """Close and re-open the port."""
        self.close()
        print(f"[{self.name}] Reconnecting to {self.port}…")
        self._connect()

    def close(self):
        """Close the serial port safely."""
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
            except Exception:
                pass
        self._serial = None

    # ─────────────────────────────────────────
    #  DATA READING
    # ─────────────────────────────────────────
    def read_bytes(self, n: int = 64) -> bytes:
        """
        Read up to n bytes from the serial port.
        Returns empty bytes if nothing available or on error.
        """
        if self._serial is None or not self._serial.is_open:
            self.reconnect()
            return b""
        try:
            waiting = self._serial.in_waiting
            if waiting > 0:
                return self._serial.read(min(n, waiting))
            return b""
        except serial.SerialException as e:
            print(f"[{self.name}] Read error: {e}")
            raise  # Let main.py handle reconnect logic

    def is_connected(self) -> bool:
        """Return True if the port is open."""
        return self._serial is not None and self._serial.is_open

    def flush_input(self):
        """Clear any stale bytes in the input buffer."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
