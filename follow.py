#!/usr/bin/env python3
"""Follow one coloured stripe of the track, stop before obstacles.

The three stripes touch side by side (config.TRACK_ORDER), so drifting
off the target lands the sensor on a neighbour, and the neighbour says
which side it drifted to. Turns stop one wheel instead of reversing it,
as the lab page suggests: the sensor sits near the axle.

  python3 follow.py                     blue at 30 rpm for 20 s
  python3 follow.py red 30 20           red at 30 rpm for 20 s
  python3 follow.py red 30 20 reverse   the track driven the other way
  python3 follow.py blue 30 90 forward 0   distance stop off, for testing

Driving the track the other way round swaps which stripe is on the left,
so "reverse" flips config.TRACK_ORDER.

Every loop is logged to follow_<colour>_<rpm>_<direction>_<time>.csv.
Ctrl+C stops it, so does the e-stop button.
"""

import csv
import sys
import time

import config
from colour import ColourSensor, classify, edge_side, side_of
from distance import Distance
from estop import EStop
from rover import disconnect, Rover, SpeedController, Wheel

TARGET = sys.argv[1] if len(sys.argv) > 1 else "blue"
RPM = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
DURATION = float(sys.argv[3]) if len(sys.argv) > 3 else 20.0
DIRECTION = sys.argv[4] if len(sys.argv) > 4 else "forward"
STOP_CM = float(sys.argv[5]) if len(sys.argv) > 5 else 30.0
# inner wheel speed, as a share of RPM, on the edge between two
# stripes. stopping it outright made every small drift on the straight a
# hard correction, but half speed on a whole neighbour stripe was too
# weak for the curves, it swung out onto white. 20 Oct
SOFT_TURN = 0.5

if TARGET not in config.TRACK_ORDER:
    sys.exit(f"{TARGET} is not one of {', '.join(config.TRACK_ORDER)}")
if DIRECTION not in ("forward", "reverse"):
    sys.exit(f"{DIRECTION} is not forward or reverse")
ORDER = (config.TRACK_ORDER if DIRECTION == "forward"
         else tuple(reversed(config.TRACK_ORDER)))


def steer(seen, reading, target, last_turn):
    """Decide the wheel speeds for this loop.

    seen is what the sensor reads now: "white", "grey", "red", "green"
    or "blue", and reading the raw (red, green, blue, clear) it came
    from. side_of(seen, target) says where the sensor has drifted:
    "left", "right", or None when on the target or it cannot tell.
    last_turn is the last correction made: "left", "right" or None.

    Returns (left_rpm, right_rpm, turn). The turn grows with the drift:
    on an edge the inner wheel slows to SOFT_TURN, on a neighbour stripe
    or white past the outer stripes it stops.
    """
    if seen == target:
        # keep the last correction as memory: if the line is lost next,
        # the curve most likely bends the way it was last corrected
        return RPM, RPM, last_turn
    side = side_of(seen, target, ORDER)
    inner = 0.0
    if seen == "grey":
        # an edge between two stripes: the mix says which side, so turn
        # softly before the reading becomes the neighbour
        side = edge_side(reading, target, ORDER)
        inner = RPM * SOFT_TURN
    if side == "left":
        turn = "right"
    elif side == "right":
        turn = "left"
    elif last_turn is not None:
        # no colour says where: keep turning the same way. on white, past
        # the outer stripes, that turn stays hard
        turn = last_turn
    else:
        return RPM, RPM, None
    if turn == "right":
        return RPM, inner, turn
    return inner, RPM, turn

estop = EStop()
rover = Rover(estop)
left = Wheel(config.LEFT_ENCODER)
right = Wheel(config.RIGHT_ENCODER)
control = SpeedController(rover, left, right)
sensor = Distance()
colour = ColourSensor()

print(f"follow {TARGET} at {RPM:.0f} rpm ({config.rpm_to_cm_s(RPM):.0f} cm/s) "
      f"for {DURATION:.0f} s, "
      f"{'distance stop off' if STOP_CM <= 0 else f'stop at {STOP_CM:.0f} cm'}, "
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
        if STOP_CM > 0 and not stopped and cm is not None and cm <= STOP_CM:
            stopped = True
            control.stop()
            print(f"{time.monotonic() - start:5.2f} s  STOP  {cm:.0f} cm")

        if not stopped:
            left_rpm, right_rpm, turn = steer(seen, reading, TARGET, turn)
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
