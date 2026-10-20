#!/usr/bin/env python3
"""Spin the wheel the code calls left, then the one it calls right.

Labs 7 and 9 always drove both wheels at the same speed, so a swap
between the code's left and the physical left would never have shown.
Line following stops one wheel to turn, so it has to be right.

Wheels off the ground. Run on the Pi:  python3 wheeltest.py
"""

import time

from estop import EStop
from rover import disconnect, Rover

DUTY = 0.3
SPIN_SECONDS = 2.0

estop = EStop()
rover = Rover(estop)
try:
    estop.arm()
    for name, motor in (("LEFT", rover.left_motor), ("RIGHT", rover.right_motor)):
        print(f"code's {name} wheel spinning")
        motor.forward(DUTY)
        time.sleep(SPIN_SECONDS)
        motor.stop()
        time.sleep(1.0)
finally:
    rover.stop()
    estop.close()
    disconnect()
