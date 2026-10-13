"""Emergency stop. Owns the DRV8833 sleep line."""

from gpiozero import Button, DigitalOutputDevice

import config


class EStop:
    """Latching stop.

    Drops SLP so the driver is disabled at the chip rather than by
    commanding the motors, so it still works if the control loop is
    busy or wedged.
    """

    def __init__(self, stop_pin=config.STOP_PIN, sleep_pin=config.SLEEP_PIN):
        self._slp = DigitalOutputDevice(sleep_pin)
        self._button = Button(stop_pin, pull_up=True,
                              bounce_time=config.DEBOUNCE)
        self._latched = False
        self._button.when_pressed = self.trip

    @property
    def armed(self):
        return not self._latched

    def arm(self):
        """Power the driver up. Called once at startup."""
        self._slp.on()

    def trip(self):
        """Latch the stop and kill the driver.

        Runs on gpiozero's button thread, not the main loop.
        """
        # hardware first: if anything goes wrong after this line the
        # rover is already stopped
        self._slp.off()
        self._latched = True

    def rearm(self):
        """Clear the latch and power the driver back up."""
        # latch cleared last, so the control loop cannot issue a drive
        # command until the driver is actually powered
        self._slp.on()
        self._latched = False

    def close(self):
        self._slp.off()
