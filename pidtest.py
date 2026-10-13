#!/usr/bin/env python3
"""Hold a target speed with the PID and print what both wheels do.

WHEELS OFF THE GROUND for the first runs. The lab warns the controller
can oscillate or run away, so keep a hand near the stop button.

  python3 pidtest.py                    150 rpm for 15 s, config gains
  python3 pidtest.py 80                 80 rpm for 15 s
  python3 pidtest.py 80 4               80 rpm for 4 s
  python3 pidtest.py 80 4 0.002 0.004 0 and these gains

Arguments are target, duration, then Kp Ki Kd. Overriding the gains on
the command line means tuning does not need an edit and a push each
time.

On the floor, distance is target / 60 * duration * 15.1 cm. 80 rpm for
4 s is about 80 cm.

Ctrl+C stops it, so does the e-stop button.
"""

import csv
import sys
import time

import config
from estop import EStop
from rover import disconnect, Rover, SpeedController, Wheel

TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else 150.0
DURATION = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
GAINS = tuple(float(a) for a in sys.argv[3:6]) if len(sys.argv) > 5 else None

estop = EStop()
rover = Rover(estop)
left = Wheel(config.ENCODER_PIN_A)
right = Wheel(config.ENCODER_PIN_B)
control = SpeedController(rover, left, right, GAINS)

kp, ki, kd = control.tunings
turns = TARGET / 60 * DURATION
print(f"target {TARGET:.0f} rpm for {DURATION:.0f} s, about {turns:.0f} "
      f"wheel turns   Kp {kp}  Ki {ki}  Kd {kd}")
print(f"target is {config.rpm_to_cm_s(TARGET):.0f} cm/s on a "
      f"{config.WHEEL_DIAMETER_CM} cm wheel")
print("   t   left rpm  left duty   right rpm  right duty    cm/s")

name = f"pid_{TARGET:.0f}_{kp}_{ki}_{kd}.csv"
rows = []

try:
    estop.arm()
    control.target(TARGET)
    start = time.monotonic()
    while time.monotonic() - start < DURATION:
        time.sleep(config.CONTROL_INTERVAL)
        (lr, ld), (rr, rd) = control.update()
        t = time.monotonic() - start
        cm_s = config.rpm_to_cm_s((lr + rr) / 2)
        rows.append((round(t, 3), round(lr, 1), round(ld, 4),
                     round(rr, 1), round(rd, 4)))
        print(f"{t:5.1f} {lr:10.1f} {ld:10.3f}  {rr:10.1f} {rd:10.3f}"
              f" {cm_s:7.1f}")
    control.stop()
    with open(name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "left_rpm", "left_duty", "right_rpm", "right_duty"])
        w.writerows(rows)
    print(f"wrote {name}")
finally:
    estop.close()
    left.close()
    right.close()
    disconnect()
