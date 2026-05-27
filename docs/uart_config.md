# UART Configuration Guide

## Final Working Configuration

Edit `/boot/config.txt` on your Raspberry Pi:

```bash
sudo nano /boot/config.txt
```

Add these lines at the **bottom** of the file:

```ini
# Enable primary UART on GPIO14/15 (ttyAMA0)
enable_uart=1

# Disable Bluetooth so ttyAMA0 is fully available (not shared with BT)
dtoverlay=disable-bt

# Enable UART3 on GPIO4 (TX) and GPIO5 (RX)
dtoverlay=uart3,txd3_pin=4,rxd3_pin=5

# Enable UART4 on GPIO12 (TX) and GPIO13 (RX)
dtoverlay=uart4,txd4_pin=12,rxd4_pin=13
```

Save with `Ctrl+X → Y → Enter`, then reboot:

```bash
sudo reboot
```

---

## Why Each Line Is Needed

| Line | Purpose |
|---|---|
| `enable_uart=1` | Activates the primary PL011 UART hardware on GPIO14/15 → `/dev/ttyAMA0` |
| `dtoverlay=disable-bt` | Frees the PL011 from Bluetooth use; without this, ttyAMA0 is used by BT and becomes unreliable |
| `dtoverlay=uart3,txd3_pin=4,rxd3_pin=5` | Enables UART3 on GPIO4 (TX) and GPIO5 (RX) → `/dev/ttyAMA3` |
| `dtoverlay=uart4,txd4_pin=12,rxd4_pin=13` | Enables UART4 on GPIO12 (TX) and GPIO13 (RX) → `/dev/ttyAMA4` |

> Note: Do **not** add `dtoverlay=uart0` — it conflicts with `enable_uart=1` and will break ttyAMA0.

---

## Disable Serial Console (Required)

By default the Pi uses ttyAMA0 as a login console. Disable it:

```bash
sudo raspi-config
```

Navigate: `Interface Options → Serial Port`
- **Login shell over serial?** → **No**
- **Enable serial hardware?** → **Yes**

Exit and reboot.

---

## Verify After Reboot

```bash
ls /dev/ttyAMA*
```

Expected output:
```
/dev/ttyAMA0
/dev/ttyAMA3
/dev/ttyAMA4
```

Also check kernel messages:
```bash
dmesg | grep tty
```

You should see lines like:
```
fe201000.serial: ttyAMA0 at MMIO ...
fe201600.serial: ttyAMA3 at MMIO ...
fe201800.serial: ttyAMA4 at MMIO ...
```

---

## UART to Device Mapping

| UART Device | GPIO TX | GPIO RX | Pi Header Pin (TX/RX) | Sensor |
|---|---|---|---|---|
| `/dev/ttyAMA0` | GPIO14 | GPIO15 | Pin 8 / Pin 10 | Sensor 1 |
| `/dev/ttyAMA3` | GPIO4 | GPIO5 | Pin 7 / Pin 29 | Sensor 2 |
| `/dev/ttyAMA4` | GPIO12 | GPIO13 | Pin 32 / Pin 35 | Sensor 3 |

---

## Permission Fix

If you get `Permission denied` opening the port:

```bash
sudo usermod -aG dialout $USER
# Then log out and log back in (or reboot)
```

Or run the script with sudo temporarily to test:
```bash
sudo python3 src/main.py
```
