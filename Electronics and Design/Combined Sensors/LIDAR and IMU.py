import time
import math
import numpy as np
import smbus
from adafruit_extended_bus import ExtendedI2C as I2C
import adafruit_bno055

# To enable i2c-gpio, add the line `dtoverlay=i2c-gpio` to /boot/config.txt
# Then reboot the pi

# Create library object using our Extended Bus I2C port
# Use `ls /dev/i2c*` to find out what i2c devices are connected

I2C_BUS = 1
I2C_ADDRESS = 0x31

bus = smbus.SMBus(I2C_BUS)

i2c = I2C(1)  # Device is /dev/i2c-1
sensor = adafruit_bno055.BNO055_I2C(i2c)

last_val = 0xFFFF

def temperature():
    global last_val  # pylint: disable=global-statement
    result = sensor.temperature

    if abs(result - last_val) == 128:
        result = sensor.temperature
        if abs(result - last_val) == 128:
            return 0b00111111 & result

    last_val = result
    return result

def quartenion_to_euler(x, y, z, w):
    t0 = +2.0*(w*x + y*z)
    t1 = +1.0 - 2.0*(x*x + y*y)
    roll_x = math.atan2(t0, t1)

    t2 = +2.0*(w*y - z*x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)

    t3 = +2.0*(w*z + x*y)
    t4 = +1.0 - 2.0*(y*y + z*z)
    yaw_z = math.atan2(t3, t4)

    return roll_x*180/math.pi, pitch_y*180/math.pi, yaw_z*180/math.pi

def read_distance():
    try:
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0, 2)

        distance = (data[0] << 8 | data[1])

        if (distance == 65535):
            return None
        return distance / 1000.0
    
    except Exception as e:
        print(f"Error reading from sensor: {e}")
        return None

while True:
    #print("Accelerometer (m/s^2): {}".format(sensor.acceleration))
    #print("Magnetometer (microteslas): {}".format(sensor.magnetic))
    #print("Gyroscope (rad/sec): {}".format(sensor.gyro))
    #print("Euler angle: {}".format(sensor.euler))
    quartenion = sensor.quaternion
    roll, pitch, yaw= quartenion_to_euler(quartenion[0], quartenion[1], quartenion[2], quartenion[3])
    print("Roll (x-axis):", round(roll, 2), "Pitch (y-axis):", round(pitch, 2), "Yaw (z-axis):", round(yaw, 2))
    #print("Linear acceleration (m/s^2): {}".format(sensor.linear_acceleration))
    #print("Gravity (m/s^2): {}".format(sensor.gravity))
    distance = read_distance()
    if (distance != None):
        print(f"Distance: {distance:.3f} m")
    else:
        print("Invalid reading")
    print()
    time.sleep(1)