import math
import os

# gpiozero resolves this when the first device is created, so setting it
# here is enough as long as config is imported before any device exists.
# pigpio also gives DMA timed PWM instead of CPU timed.
os.environ.setdefault("GPIOZERO_PIN_FACTORY", "pigpio")

MOTOR_A = {"forward": "GPIO12", "backward": "GPIO13"}
MOTOR_B = {"forward": "GPIO19", "backward": "GPIO18"}

# both encoder channels, kept for reference. we no longer read the B
# channel: decoding quadrature in Python could not keep up, see
# ENCODER_PIN_A below
ENCODER_A = ("GPIO5", "GPIO6")
ENCODER_B = ("GPIO16", "GPIO26")

# C1 only, one channel per wheel. counted by pigpio's tally in C, which
# never wakes Python. no direction, the commanded direction gives that
ENCODER_PIN_A = "GPIO5"
# GPIO16 is motor B's C1 on paper but reads no edges at all, 13 Oct, so
# the right wheel uses C2 instead. likely a loose jumper on Pi pin 36.
# single channel counting does not care which of the two it uses
ENCODER_PIN_B = "GPIO26"

SLEEP_PIN = "GPIO25"
STOP_PIN = "GPIO4"
IR_CHANNEL = 0

# measured 13 Oct with calibrate.py over 5 hand turns per wheel:
# left 3475 edges, right 3450, so (3475 + 3450) / 10. the two agree to
# 0.7 percent, inside hand turning error, so one constant serves both.
# the Lab 6 page's "about 700 pulses" is one channel's rising edges,
# not the quadrature total
PULSES_PER_REV = 693

SPEED = 0.5

# the terminal waits before it starts repeating a held key, so the first
# press gets a long grace period and the rest get a short one
STOP_AFTER = 0.1
FIRST_HOLD = 0.7
REPEAT_GAP = 0.25

DEBOUNCE = 0.05

# --- speed control -------------------------------------------------
# control loop period. at 150 rpm and 693 pulses a revolution a 0.05 s
# window holds about 87 pulses, so speed is quantised to about 1 percent
CONTROL_INTERVAL = 0.05

# measured 13 Oct, wheels off the ground, duty to rpm:
#   0.05   15 / 10      0.25   175 / 177
#   0.10   91 / 96      0.30   187 / 189
#   0.15  134 / 138     0.50   212 / 211
#   0.20  159 / 162     1.00   234 / 228
# the plant is steep at the bottom and nearly flat above 0.3. local gain
# near duty 0.15 is (159 - 91) / (0.20 - 0.10) = 680 rpm per unit duty,
# which is where these starting gains come from: correcting a 20 rpm
# error wants about 0.03 duty, so Kp is about 0.0015. started lower.
# TUNED 13 Oct, wheels off the ground, target 150 rpm. three runs:
#   Kp 0.001 Ki 0.002   90% in 1.7 s, no overshoot, band 147-152
#   Kp 0.002 Ki 0.004   90% in 0.3 s, slight dip,   band 146-156
#   Kp 0.004 Ki 0.008   90% in 0.2 s, overshoots to 166 then rings
#                       with a 0.35 to 0.4 s period, band 144-158
# oscillation starts at 0.004, so back off to half of it
KP = 0.002
KI = 0.004
KD = 0.0

# below about 0.05 duty the motors do not turn at all
DEADBAND = 0.05

# measured across the wheel with a ruler, 13 Oct
WHEEL_DIAMETER_CM = 4.8
WHEEL_CIRCUMFERENCE_CM = 3.14159 * WHEEL_DIAMETER_CM   # 15.1 cm


# centre to centre across the two wheels, measured 13 Oct
TRACK_CM = 10.8


def rpm_to_cm_s(rpm):
    """Wheel speed in rpm to ground speed in cm per second."""
    return rpm / 60 * WHEEL_CIRCUMFERENCE_CM


def turn_rate_deg_s(left_rpm, right_rpm, track_cm=TRACK_CM):
    """Signed wheel speeds to how fast the rover rotates, degrees/s.

    Positive is a left turn. A spin on the spot is equal and opposite
    wheel speeds, which gives twice the rate of one wheel alone.
    """
    diff = rpm_to_cm_s(right_rpm) - rpm_to_cm_s(left_rpm)
    return math.degrees(diff / track_cm)

