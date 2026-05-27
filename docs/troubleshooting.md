# Troubleshooting Guide

## Problem 1: `/dev/ttyAMA*` not appearing after reboot

**Symptoms:** `ls /dev/ttyAMA*` returns "No such file or directory"

**Causes & Fixes:**

1. **Wrong config.txt syntax** — check for spaces around `=` signs. There must be none:
   ```
   # WRONG
   dtoverlay = uart3, txd3_pin = 4
   
   # CORRECT
   dtoverlay=uart3,txd3_pin=4,rxd3_pin=5
   ```

2. **Conflicting `dtoverlay=uart0`** — remove that line. `enable_uart=1` already handles UART0.

3. **Serial console still active** — run `sudo raspi-config` → Interface Options → Serial Port → disable login shell, enable hardware.

4. **Wrong boot partition** — on newer Pi OS the file may be `/boot/firmware/config.txt`:
   ```bash
   ls /boot/firmware/config.txt   # check if this exists
   sudo nano /boot/firmware/config.txt
   ```

5. **Verify overlays loaded:**
   ```bash
   dtoverlay -l
   ```
   Should show `uart3` and `uart4` in the list.

---

## Problem 2: `Permission denied` on `/dev/ttyAMA*`

```bash
sudo usermod -aG dialout $USER
# Reboot or log out and in again
```

Test immediately with sudo:
```bash
sudo python3 src/main.py
```

---

## Problem 3: Sensor not responding (no data / all zeros)

**Check TX/RX wiring — they must be crossed:**
- Sensor OT1 (TX) → Pi RX pin
- Sensor RX → Pi TX pin

**Check baud rate** — LD2410S defaults to **256000 baud**. Some modules ship at 115200. Test both:
```python
# In main.py, try changing:
BAUD_RATE = 115200   # first attempt
BAUD_RATE = 256000   # second attempt
```

**Check with minicom (manual test):**
```bash
sudo apt install minicom
sudo minicom -D /dev/ttyAMA0 -b 256000
```
You should see binary data scrolling. Press `Ctrl+A → Q` to exit.

---

## Problem 4: Raspberry Pi showing undervoltage warning (⚡ lightning bolt)

- Use a **5V 3A** power supply minimum
- Use the **original Samsung USB-C cable** (PD-rated)
- Avoid cheap USB hubs or extension cables
- Your Samsung EP-TA800 charger confirmed working at 5V 3A

---

## Problem 5: `pyserial` install error (externally-managed-environment)

Do **not** use pip directly. Use apt instead:
```bash
sudo apt update
sudo apt install python3-serial
```

Or use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install pyserial
```

---

## Problem 6: Only some UARTs detected (e.g. ttyAMA0 but not ttyAMA3/4)

Verify:
1. Both overlay lines are in config.txt with exact pin numbers
2. Pi firmware is up to date:
   ```bash
   sudo apt update && sudo apt full-upgrade
   sudo rpi-update   # updates firmware
   sudo reboot
   ```

---

## Problem 7: Web dashboard not loading

- Check the Pi's IP address: `hostname -I`
- Open browser on same network: `http://172.20.10.4:8000`
- Check if port 8000 is blocked: `sudo ufw status`
- If using mobile hotspot, make sure phone and Pi are on same hotspot network

---

## Problem 8: Script crashes or freezes

Run with verbose output:
```bash
python3 src/main.py 2>&1 | tee run.log
```

Check `run.log` for error messages. Common causes:
- UART port disconnected → handled by retry logic automatically
- Memory issues (unlikely) → reboot Pi
