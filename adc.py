"""MCP3008 over pigpio's SPI.

Labs 4 and 7 read this chip through Adafruit Blinka, which lives in a
separate virtualenv from gpiozero and pigpio. Lab 9 needs the distance
sensor and the motors in one program, so the ADC is read here through
pigpio instead and the two interpreters stop mattering.

Protocol: three bytes out, three back. The first byte is a start bit,
the second selects single ended mode and the channel in its top nibble,
the third clocks the answer out. The 10 bit result is the low 2 bits of
the second byte returned plus all of the third.
"""

import pigpio

import rover

SPI_CHANNEL = 0        # CE0, Pi pin 24
SPI_SPEED = 1_000_000  # the MCP3008 tops out near 1.35 MHz at 3.3V
VREF = 3.3
FULL_SCALE = 1023


class MCP3008:
    def __init__(self, spi_channel=SPI_CHANNEL, speed=SPI_SPEED):
        self._pi = rover._connect()
        self._handle = self._pi.spi_open(spi_channel, speed, 0)

    def read(self, channel):
        """Raw count, 0 to 1023, from one single ended input."""
        if not 0 <= channel <= 7:
            raise ValueError(f"channel {channel} is not 0 to 7")
        _, rx = self._pi.spi_xfer(self._handle, [0x01, (0x08 | channel) << 4, 0x00])
        return ((rx[1] & 0x03) << 8) | rx[2]

    def volts(self, channel):
        return self.read(channel) * VREF / FULL_SCALE

    def close(self):
        self._pi.spi_close(self._handle)
