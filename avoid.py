#!/usr/bin/env python3
"""Drive forward under speed control and stop before hitting anything.

Policy A, hard stop: hold the target speed until the distance sensor
reads STOP_CM or less, then stop.

  python3 avoid.py                 80 rpm for 10 s, stop at 30 cm
  python3 avoid.py 80 10 35        80 rpm for 10 s, stop at 35 cm

Every loop is logged to avoid_<rpm>_<stop>.csv. Only stop and go
events are printed, since printing every loop slowed Lab 7's loop
from 50 to 77 ms.

Ctrl+C stops it, so does the e-stop button.
"""

import csv
import sys
import time

import config
from distance import Distance
from estop import EStop
from rover import disconnect, Rover, SpeedController, Wheel

TARGET = float(sys.argv[1]) if len(sys.argv) > 1 else 80.0
DURATION = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
STOP_CM = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0


def should_stop(cm, stopped):
    """Decide, once per loop, whether the rover must be stopped.

    cm is the distance ahead: 0 means too close to measure (under about
    19 cm), None means nothing in range. stopped is what this function
    returned last loop.
    """
    # latched: once stopped it stays stopped until the run ends, so noise
    # around STOP_CM can never let it creep forward again
    if stopped:
        return True
    return cm is not None and cm <= STOP_CM


estop = EStop()
rover = Rover(estop)
left = Wheel(config.ENCODER_PIN_A)
right = Wheel(config.ENCODER_PIN_B)
control = SpeedController(rover, left, right)
sensor = Distance()

print(f"target {TARGET:.0f} rpm ({config.rpm_to_cm_s(TARGET):.0f} cm/s) "
      f"for {DURATION:.0f} s, stop at {STOP_CM:.0f} cm")

name = f"avoid_{TARGET:.0f}_{STOP_CM:.0f}.csv"
rows = []
stopped = False

try:
    estop.arm()
    control.target(TARGET)
    start = time.monotonic()
    while time.monotonic() - start < DURATION:
        time.sleep(config.CONTROL_INTERVAL)
        volts, cm = sensor.read()

        now_stopped = should_stop(cm, stopped)
        if now_stopped != stopped:
            t = time.monotonic() - start
            shown = "out of range" if cm is None else f"{cm:.0f} cm"
            print(f"{t:5.2f} s  {'STOP' if now_stopped else 'GO'}  {shown}")
            if now_stopped:
                control.stop()
            else:
                control.target(TARGET)
        stopped = now_stopped

        (lr, ld), (rr, rd) = control.update()
        t = time.monotonic() - start
        rows.append((round(t, 3), round(volts, 3),
                     "" if cm is None else round(cm, 1), int(stopped),
                     round(lr, 1), round(ld, 4), round(rr, 1), round(rd, 4)))
    control.stop()
finally:
    with open(name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "volts", "cm", "stopped",
                    "left_rpm", "left_duty", "right_rpm", "right_duty"])
        w.writerows(rows)
    print(f"wrote {name}, {len(rows)} rows")
    estop.close()
    sensor.close()
    left.close()
    right.close()
    disconnect()
