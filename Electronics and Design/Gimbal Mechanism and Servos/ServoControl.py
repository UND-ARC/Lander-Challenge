#This code is no longer used as the pigpio library is more accurate


import RPi.GPIO as GPIO
import time

# Define the GPIO pin
SERVO_PIN = 14
angle = 0

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(SERVO_PIN, GPIO.OUT)

# Initialize PWM with 50Hz (standard for servos)
pwm = GPIO.PWM(SERVO_PIN, 50)
pwm.start(0)

def set_angle(angle):
    """Convert angle (0-180) to duty cycle and move servo"""
    duty = 2 + (angle / 18)  # Convert angle to duty cycle (2-12 range)
    GPIO.output(SERVO_PIN, True)
    pwm.ChangeDutyCycle(duty)
    time.sleep(0.5)  # Allow servo to reach position
    GPIO.output(SERVO_PIN, False)
    pwm.ChangeDutyCycle(0)

try:
    while angle <= 180:
        set_angle(angle)
        print("Angle:", angle)
        time.sleep(0.1)
        angle = angle + 1
        
except KeyboardInterrupt:
    print("Exiting...")
finally:
    pwm.stop()
    GPIO.cleanup()
