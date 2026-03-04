import time
import board
import busio

from adafruit_bno055 import BNO055_I2C
from adafruit_mpl3115a2 import MPL3115A2

# =========================
# I2C SETUP
# =========================
i2c = busio.I2C(board.SCL, board.SDA)

# =========================
# SENSOR INIT
# =========================

# BNO055 sensors
bno1 = BNO055_I2C(i2c, address=0x28)  # ADR low
bno2 = BNO055_I2C(i2c, address=0x29)  # ADR high

# MPL3115A2 sensor
mpl = MPL3115A2(i2c, address=0x60)

print("Sensors initialized.")
print("Reading every 5 seconds...\n")

# =========================
# MAIN LOOP
# =========================
while True:
    try:
        # ----- BNO055 #1 -----
        euler1 = bno1.euler
        accel1 = bno1.acceleration

        # ----- BNO055 #2 -----
        euler2 = bno2.euler
        accel2 = bno2.acceleration

        # ----- MPL3115A2 -----
        pressure = mpl.pressure
        altitude = mpl.altitude
        temperature = mpl.temperature

        # =====================
        # PRINT DATA
        # =====================
        print("=== BNO055 #1 ===")
        print(f"Euler: {euler1}")
        print(f"Accel: {accel1}")

        print("\n=== BNO055 #2 ===")
        print(f"Euler: {euler2}")
        print(f"Accel: {accel2}")

        print("\n=== MPL3115A2 ===")
        print(f"Pressure: {pressure:.2f} hPa")
        print(f"Altitude: {altitude:.2f} m")
        print(f"Temp: {temperature:.2f} C")

        print("\n-----------------------------\n")

    except Exception as e:
        print("Read error:", e)

    time.sleep(5)