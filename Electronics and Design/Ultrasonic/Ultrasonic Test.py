import time
import RPi.GPIO as GPIO


PIN_TRIGGER = 18

PIN_ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(PIN_TRIGGER, GPIO.OUT)
GPIO.setup(PIN_ECHO, GPIO.IN)

def measure_distance():
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
    distance = round((pulse_duration * 34300)/2, 2)
    
    return distance

try:
    while True:
        distance = measure_distance()
        inch = round(distance / 2.54, 2)
        feet = round(inch / 12, 2)
        print("Distance:", distance, "cm", inch, "in", feet, "ft")
        time.sleep(1)

except KeyboardInterrupt:
    print("Measurement stopped")
    GPIO.cleanup()