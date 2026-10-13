#!/usr/bin/env python3
"""Print the IR sensor through pigpio's SPI, twice a second.

Compare against raw.py in the cpsy-lab4 repo, which reads the same chip
through Adafruit Blinka. The numbers should agree.

Run on the Pi:  python3 adctest.py
Ctrl+C stops it.
"""

import time

import config
from adc import MCP3008
from rover import disconnect

adc = MCP3008()
print(f"MCP3008 channel {config.IR_CHANNEL}, through pigpio")
try:
    while True:
        raw = adc.read(config.IR_CHANNEL)
        print(f"raw {raw:4d}   volts {raw * 3.3 / 1023:5.3f}")
        time.sleep(0.5)
except KeyboardInterrupt:
    pass
finally:
    adc.close()
    disconnect()
