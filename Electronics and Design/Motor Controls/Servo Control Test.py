import time
import board
import busio
from adafruit_pca9685 import PCA9685

# =========================
# USER CALIBRATION
# =========================
I2C_ADDRESS = 0x40  # change later
PWM_FREQ = 60       # your specified frequency

# Your measured pulse widths (milliseconds)
PULSE_MIN_MS = 0.560   # -90°
PULSE_MID_MS = 1.460   # 0°
PULSE_MAX_MS = 2.350   # +90°

# Servo channels
SERVO1_CH = 0
SERVO2_CH = 1

# =========================
# SETUP
# =========================
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c, address=I2C_ADDRESS)
pca.frequency = PWM_FREQ

PERIOD_MS = 1000.0 / PWM_FREQ  # 16.6667 ms


# =========================
# CONVERSION FUNCTIONS
# =========================
def pulse_ms_to_counts(pulse_ms):
    """Convert pulse width in ms to PCA9685 counts."""
    return int((pulse_ms / PERIOD_MS) * 4096)


def angle_to_counts(angle_deg):
    """
    Map -90..+90 degrees → calibrated pulse width → PCA counts
    """
    angle_deg = max(-90, min(90, angle_deg))

    # linear interpolation between min and max
    pulse = (
        PULSE_MIN_MS
        + (angle_deg + 90) / 180.0 * (PULSE_MAX_MS - PULSE_MIN_MS)
    )

    return pulse_ms_to_counts(pulse)


def set_servo_angle(channel, angle_deg):
    counts = angle_to_counts(angle_deg)
    pca.channels[channel].duty_cycle = counts << 4  # PCA expects 16-bit


# =========================
# TEST ROUTINE
# =========================
try:
    print("Testing calibrated servo motion...")

    set_servo_angle(SERVO1_CH, -90)
    set_servo_angle(SERVO2_CH, -90)
    time.sleep(5)

    set_servo_angle(SERVO1_CH, 0)
    set_servo_angle(SERVO2_CH, 0)
    time.sleep(5)

    set_servo_angle(SERVO1_CH, 90)
    set_servo_angle(SERVO2_CH, 90)
    time.sleep(5)

finally:
    pca.deinit()
    print("Done.")