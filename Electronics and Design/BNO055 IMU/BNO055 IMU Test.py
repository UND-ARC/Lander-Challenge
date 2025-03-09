import time

from adafruit_extended_bus import ExtendedI2C as I2C

import adafruit_bno055


# To enable i2c-gpio, add the line `dtoverlay=i2c-gpio` to /boot/config.txt

# Then reboot the pi


# Create library object using our Extended Bus I2C port

# Use `ls /dev/i2c*` to find out what i2c devices are connected

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



while True:

    print("Temperature: {} degrees C".format(temperature()))

    print("Accelerometer (m/s^2): {}".format(sensor.acceleration))

    print("Magnetometer (microteslas): {}".format(sensor.magnetic))

    print("Gyroscope (rad/sec): {}".format(sensor.gyro))

    print("Euler angle: {}".format(sensor.euler))

    print("Quaternion: {}".format(sensor.quaternion))

    print("Linear acceleration (m/s^2): {}".format(sensor.linear_acceleration))

    print("Gravity (m/s^2): {}".format(sensor.gravity))

    print()


    time.sleep(1)