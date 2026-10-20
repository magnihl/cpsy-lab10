#!/usr/bin/env python3
"""Follow one coloured stripe of the track, stop before obstacles.

The three stripes touch side by side (config.TRACK_ORDER), so drifting
off the target lands the sensor on a neighbour, and the neighbour says
which side it drifted to. Turns stop one wheel instead of reversing it,
as the lab page suggests: the sensor sits near the axle.

  python3 follow.py                     blue at 30 rpm for 20 s
  python3 follow.py red 30 20           red at 30 rpm for 20 s
  python3 follow.py red 30 20 reverse   the track driven the other way

Driving the track the other way round swaps which stripe is on the left,
so "reverse" flips config.TRACK_ORDER.

Every loop is logged to follow_<colour>_<rpm>_<direction>_<time>.csv.
Ctrl+C stops it, so does the e-stop button.
"""

import csv
import sys
import time

import config
from colour import ColourSensor, classify, side_of
from distance import Distance
from estop import EStop
from rover import disconnect, Rover, SpeedController, Wheel

TARGET = sys.argv[1] if len(sys.argv) > 1 else "blue"
RPM = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
DURATION = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
DIRECTION = sys.argv[4] if len(sys.argv) > 4 else "forward"
STOP_CM = 30.0

if TARGET not in config.TRACK_ORDER:
    sys.exit(f"{TARGET} is not one of {', '.join(config.TRACK_ORDER)}")
if DIRECTION not in ("forward", "reverse"):
    sys.exit(f"{DIRECTION} is not forward or reverse")
ORDER = (config.TRACK_ORDER if DIRECTION == "forward"
         else tuple(reversed(config.TRACK_ORDER)))


def steer(seen, target, last_turn):
    """Decide the wheel speeds for this loop.

    seen is what the sensor reads now: "white", "grey", "red", "green"
    or "blue". side_of(seen, target) says where the sensor has drifted:
    "left", "right", or None when on the target or it cannot tell.
    last_turn is the last correction made: "left", "right" or None.

    Returns (left_rpm, right_rpm, turn). To turn right, stop the right
    wheel and drive the left one at RPM; to turn left, the opposite.
    """
    side = side_of(seen, target, ORDER)
    if seen == target:
        # keep the last correction as memory: if the line is lost next,
        # the curve most likely bends the way it was last corrected
        return RPM, RPM, last_turn
    if side == "left":
        turn = "right"
    elif side == "right":
        turn = "left"
    else:
        # lost and no neighbour to say where: keep turning the same way,
        # or creep straight if there has been no correction yet
        if last_turn is None:
            return RPM, RPM, None
        turn = last_turn
    if turn == "right":
        return RPM, 0.0, turn
    return 0.0, RPM, turn


estop = EStop()
rover = Rover(estop)
left = Wheel(config.ENCODER_PIN_A)
right = Wheel(config.ENCODER_PIN_B)
control = SpeedController(rover, left, right)
sensor = Distance()
colour = ColourSensor()

print(f"follow {TARGET} at {RPM:.0f} rpm ({config.rpm_to_cm_s(RPM):.0f} cm/s) "
      f"for {DURATION:.0f} s, stop at {STOP_CM:.0f} cm, "
      f"stripes left to right {' '.join(ORDER)}")

name = f"follow_{TARGET}_{RPM:.0f}_{DIRECTION}_{time.strftime('%H%M%S')}.csv"
rows = []
turn = None
stopped = False

try:
    estop.arm()
    start = time.monotonic()
    while time.monotonic() - start < DURATION:
        time.sleep(config.CONTROL_INTERVAL)
        volts, cm = sensor.read()
        reading = colour.read()
        seen = classify(reading)

        # latched, as in avoid.py: once stopped it stays stopped
        if not stopped and cm is not None and cm <= STOP_CM:
            stopped = True
            control.stop()
            print(f"{time.monotonic() - start:5.2f} s  STOP  {cm:.0f} cm")

        if not stopped:
            left_rpm, right_rpm, turn = steer(seen, TARGET, turn)
            control.target(left_rpm, right_rpm)

        (lr, ld), (rr, rd) = control.update()
        t = time.monotonic() - start
        rows.append((round(t, 3), *reading, seen, turn or "",
                     "" if cm is None else round(cm, 1), int(stopped),
                     round(lr, 1), round(ld, 4), round(rr, 1), round(rd, 4)))
    control.stop()
finally:
    with open(name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "red", "green", "blue", "clear", "seen", "turn",
                    "cm", "stopped",
                    "left_rpm", "left_duty", "right_rpm", "right_duty"])
        w.writerows(rows)
    print(f"wrote {name}, {len(rows)} rows")
    estop.close()
    sensor.close()
    colour.close()
    left.close()
    right.close()
    disconnect()
