#!/usr/bin/env python3
"""Print the colour sensor through pigpio's I2C, twice a second.

Compare against the Lab 2 Blinka reading (Exhibit 10A). The raw numbers
should agree, and the name should match the stripe under the sensor.

Run on the Pi:  python3 colourtest.py white
The word names the log, colour_white_<time>.csv. Ctrl+C stops it.
"""

import csv
import sys
import time

from colour import ColourSensor, classify
from rover import disconnect

LABEL = sys.argv[1] if len(sys.argv) > 1 else "test"

sensor = ColourSensor()
name = f"colour_{LABEL}_{time.strftime('%H%M%S')}.csv"
rows = []
start = time.monotonic()
try:
    while True:
        reading = sensor.read()
        seen = classify(reading)
        r, g, b, c = reading
        print(f"R {r:5d}  G {g:5d}  B {b:5d}  clear {c:5d}   {seen}")
        rows.append((round(time.monotonic() - start, 3), r, g, b, c, seen))
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    with open(name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["t", "red", "green", "blue", "clear", "seen"])
        w.writerows(rows)
    print(f"wrote {name}, {len(rows)} rows")
    sensor.close()
    disconnect()
