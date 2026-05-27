# Hardware Setup

## Components Required

| Component | Quantity | Notes |
|---|---|---|
| Raspberry Pi 4B | 1 | Any RAM variant works |
| LD2410S mmWave Radar Sensor | 3 | 3.3V logic, UART output |
| Samsung EP-TA800 charger (5V 3A) | 1 | Or any 5V 3A USB-C supply |
| Samsung USB-C to USB-C cable | 1 | PD-rated, original recommended |
| Jumper wires (female-female) | ~15 | For GPIO connections |
| Breadboard (optional) | 1 | For clean 3.3V/GND distribution |

---

## LD2410S Pin Description

Each LD2410S sensor has 5 pins on connector J2:

| Pin | Label | Description |
|---|---|---|
| 1 | 3V3 | 3.3V power input |
| 2 | GND | Ground |
| 3 | OT1 | UART TX output (0–3.3V logic) |
| 4 | RX | UART RX input (0–3.3V logic) |
| 5 | OT2 | Auxiliary output (not used here) |

> No level shifter needed — Pi GPIO is 3.3V, sensor is 3.3V.

---

## GPIO Wiring Table

```
Raspberry Pi 4B GPIO Header (40 pins)

SENSOR 1 → UART0 (/dev/ttyAMA0)
  LD2410S Pin 1 (3V3) → Pi Pin 1  (3.3V)
  LD2410S Pin 2 (GND) → Pi Pin 6  (GND)
  LD2410S Pin 3 (OT1) → Pi Pin 10 (GPIO15 / RXD0)   ← sensor TX → Pi RX
  LD2410S Pin 4 (RX)  → Pi Pin 8  (GPIO14 / TXD0)   ← Pi TX → sensor RX

SENSOR 2 → UART3 (/dev/ttyAMA3)
  LD2410S Pin 1 (3V3) → Pi Pin 1  (3.3V) [shared]
  LD2410S Pin 2 (GND) → Pi Pin 9  (GND)  [shared]
  LD2410S Pin 3 (OT1) → Pi Pin 29 (GPIO5 / RXD3)    ← sensor TX → Pi RX
  LD2410S Pin 4 (RX)  → Pi Pin 7  (GPIO4 / TXD3)    ← Pi TX → sensor RX

SENSOR 3 → UART4 (/dev/ttyAMA4)
  LD2410S Pin 1 (3V3) → Pi Pin 17 (3.3V) [shared]
  LD2410S Pin 2 (GND) → Pi Pin 14 (GND)  [shared]
  LD2410S Pin 3 (OT1) → Pi Pin 35 (GPIO13 / RXD4)   ← sensor TX → Pi RX
  LD2410S Pin 4 (RX)  → Pi Pin 32 (GPIO12 / TXD4)   ← Pi TX → sensor RX
```

### Quick Reference: Pi Header Pin Numbers

```
                    3V3  [1] [2]  5V
              GPIO2/SDA  [3] [4]  5V
              GPIO3/SCL  [5] [6]  GND
          GPIO4 (TXD3)  [7] [8]  GPIO14 (TXD0)
                    GND  [9][10]  GPIO15 (RXD0)
                GPIO17 [11][12]  GPIO18
                GPIO27 [13][14]  GND
                GPIO22 [15][16]  GPIO23
                   3V3 [17][18]  GPIO24
                GPIO10 [19][20]  GND
                 GPIO9 [21][22]  GPIO25
                GPIO11 [23][24]  GPIO8
                   GND [25][26]  GPIO7
               GPIO0   [27][28]  GPIO1
          GPIO5 (RXD3) [29][30]  GND
                GPIO6  [31][32]  GPIO12 (TXD4)
         GPIO13 (RXD4) [35][34]  GND
```

---

## Power Supply Notes

- Raspberry Pi 4B **requires 5V, 3A minimum**
- The Samsung EP-TA800 charger (5V @ 3A, USB-PD) confirmed working
- Use an **original USB-C to USB-C cable** (PD-rated)
- All 3 sensors share the Pi's 3.3V rail (~100 mA each, 300 mA total — within 500 mA limit)
- A **decoupling capacitor (0.1 µF)** near each sensor's 3V3/GND pins reduces noise

---

## Physical Layout Assumption (for direction estimation)

```
   [Sensor 1]    [Sensor 2]    [Sensor 3]
      LEFT         CENTER         RIGHT
       ↓              ↓              ↓
   /dev/ttyAMA0  /dev/ttyAMA3  /dev/ttyAMA4
```

Mount sensors side by side, pointing in the same direction, spaced ~30–50 cm apart.
