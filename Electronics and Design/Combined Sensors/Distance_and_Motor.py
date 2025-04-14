import time
import RPi.GPIO as GPIO
import smbus
import pigpio
from simple_pid import PID


I2C_BUS = 1
I2C_ADDRESS = 0x30

bus = smbus.SMBus(I2C_BUS)

PIN_TRIGGER = 18
PIN_ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)

ESC = 14  # Motor Startup
ESC1 = 15


pi = pigpio.pi()
pi.set_servo_pulsewidth(ESC, 0) 
pi.set_servo_pulsewidth(ESC1, 0) 
max_value = 2000                                                # Maximum Pulse
min_value = 1000                                                # Minimum Pulse

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
    if (distance > 75):
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
            distance = Ultrasonic()
        return round((distance / 10.0), 3)

    except Exception as e:
        print(f"Error reading from sensor: {e}")
        return None

'''
MAIN CODE BEGINS HERE
'''
pidThrust = PID(5.0, .6, 1.0, setpoint = 100)
pidThrust.sample_time = .75
distance = LIDAR()                                              # Start by reading LIDA
try:
    while True:
        # Measurements Here
        if (distance > 75):                                     # If over .75 meters, read from LIDAR
            print("Reading LIDAR")
            distance = LIDAR()
        else:                                                   # If distance less than 1 meter, read from Ultrasonic
            print("Reading Ultrasonic")
            distance = Ultrasonic()                          
            
        # Adjusting thrust
        speed = pidThrust(distance) + 1250
        if (speed < min_value):
            speed = min_value
        elif (speed > max_value):
            speed = max_value
        
        # Converting and printing
        inch = round(distance / 2.54, 2)
        feet = round(inch / 12, 2)
        print("Distance:", distance, "cm", inch, "in", feet, "ft")
        print("Speed:", speed, "(Pulse Width)\n")
        time.sleep(.75)

except KeyboardInterrupt:                                       # Stop code when LCtrl + C is pushed
    print("Measurement stopped")
    GPIO.cleanup()