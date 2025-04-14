import time
import RPi.GPIO as GPIO
import smbus


I2C_BUS = 1
I2C_ADDRESS = 0x30

bus = smbus.SMBus(I2C_BUS)

PIN_TRIGGER = 18
PIN_ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)

def Ultrasonic():                                               # Ultrasonic Code
    GPIO.output(PIN_TRIGGER, False)
    time.sleep(0.1)

    GPIO.output(PIN_TRIGGER, True)
    time.sleep(0.00001)
    GPIO.output(PIN_TRIGGER, False)

    GPIO.output(PIN_TRIGGER, GPIO.LOW)

    while GPIO.input(PIN_ECHO) == 0:
        pulse_start_time = time.time()
    while GPIO.input(PIN_ECHO) == 1:
        pulse_end_time = time.time()

    pulse_duration = pulse_end_time - pulse_start_time
    distance = round((pulse_duration * 34300)/2, 3)
    if (distance > 100):
        print("Error reading Ultrasonic: Switching to Lidar")
        LIDAR()
        distance = LIDAR()

    return distance

def LIDAR():                                                    # LIDAR Code
    try:
        data = bus.read_i2c_block_data(I2C_ADDRESS, 0, 2)

        distance = (data[0] << 8 | data[1])

        if (distance == 65535):
            return None
        if (distance == 0):
            print("Error reading LIDAR: Switching to Ultrasonic")
            distance = Ultrasonic() * 10
        return round((distance / 10.0), 3)

    except Exception as e:
        print(f"Error reading from sensor: {e}")
        return None

'''
MAIN CODE BEGINS HERE
'''

distance = LIDAR()                                              # Start by reading LIDAR
try:
    while True:
        # Measurements Here
        if (distance > 100):                                    # If over 1 meter, read from LIDAR
            print("Reading LIDAR")
            distance = LIDAR()
        else:                                                   # If distance less than 1 meter, read from Ultrasonic
            print("Reading Ultrasonic")
            distance = Ultrasonic()
        
        # Converting and printing
        inch = round(distance / 2.54, 2)
        feet = round(inch / 12, 2)
        print("Distance:", distance, "cm", inch, "in", feet, "ft\n")
        time.sleep(.05)

except KeyboardInterrupt:                                       # Stop code when LCtrl + C is pushed
    print("\nMeasurement stopped")
    GPIO.cleanup()