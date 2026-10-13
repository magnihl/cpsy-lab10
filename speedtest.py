#!/usr/bin/env python3
"""Print both wheels' rotations and RPM once a second.

Turn a wheel by hand, or drive the rover, and watch the numbers.

To turn a wheel by hand, leave everything plugged in and just do not
run rc.py. The motor and encoder share one cable, so unplugging the
motor unpowers the encoder. GPIO25 has an internal pull down, so with
nothing driving SLP the DRV8833 stays asleep.

Run on the Pi:  python3 speedtest.py
Ctrl+C stops it.
"""

import time

import config
from rover import disconnect, Wheel

INTERVAL = 1.0

left = Wheel(config.ENCODER_PIN_A)
right = Wheel(config.ENCODER_PIN_B)

print("  left rev   left rpm    right rev   right rpm")
try:
    while True:
        time.sleep(INTERVAL)
        lr, ls = left.rotations, left.speed()
        rr, rs = right.rotations, right.speed()
        print(f"{lr:10.2f} {ls:10.1f}   {rr:10.2f} {rs:10.1f}")
except KeyboardInterrupt:
    pass
finally:
    left.close()
    right.close()
    disconnect()
