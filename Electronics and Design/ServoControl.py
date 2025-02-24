import RPi.GPIO as GPIO
import time

# Define the GPIO pin
SERVO_PIN = 18

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
    while True:
        angle = int(input("Enter angle (0-180): "))
        if 0 <= angle <= 180:
            set_angle(angle)
        else:
            print("Invalid angle. Enter a value between 0 and 180.")
except KeyboardInterrupt:
    print("Exiting...")
finally:
    pwm.stop()
    GPIO.cleanup()
