"""IR distance sensor, GP2Y0A02YK on the MCP3008.

Same fit and limits as distance.py in cpsy-lab4, read through pigpio
instead of Blinka so it can share a program with the motors.

L = A / (V - B), fitted from 20 to 150 cm. Below about 20 cm the
sensor's output falls again, so one voltage means two distances. Above
TOO_CLOSE_V the reading is never trusted as a distance.
"""

import statistics

import config
from adc import MCP3008, VREF, FULL_SCALE

A = 48.7
B = 0.068
TOO_CLOSE_V = 2.6     # 19 cm by the fit, the edge of the valid range
OUT_OF_RANGE_V = 0.3  # nothing in front, or beyond 150 cm


class Distance:
    def __init__(self, channel=config.IR_CHANNEL, samples=10):
        self._adc = MCP3008()
        self._channel = channel
        self._samples = samples

    def volts(self):
        """Median of several samples, to reject single noisy reads."""
        raw = [self._adc.read(self._channel) for _ in range(self._samples)]
        return statistics.median(raw) * VREF / FULL_SCALE

    def read(self):
        """Return (volts, cm). cm is 0 when too close, None when out of range."""
        v = self.volts()
        if v > TOO_CLOSE_V:
            return v, 0.0
        if v < OUT_OF_RANGE_V:
            return v, None
        return v, A / (v - B)

    def close(self):
        self._adc.close()
