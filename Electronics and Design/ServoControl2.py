import pigpio
import time

servo_pin = 18

pi = pigpio.pi()
pi.set_mode(servo_pin, pigpio.OUTPUT)

def set_angle(angle):
    pulse_width = int(angle/180*2000 + 500)
    pi.set_servo_pulsewidth(servo_pin, pulse_width)

try:
    set_angle(15)
    time.sleep(1)

    set_angle(30)
    time.sleep(1)

    set_angle(45)
    time.sleep(1)

    set_angle(60)
    time.sleep(1)

    set_angle(75)
    time.sleep(1)

    set_angle(90)
    time.sleep(1)

    set_angle(105)
    time.sleep(1)

    set_angle(120)
    time.sleep(1)

    set_angle(135)
    time.sleep(1)

    set_angle(150)
    time.sleep(1)

    set_angle(165)
    time.sleep(1)

    set_angle(180)
    time.sleep(1)

except KeyboardInterrupt:
    pi.stop()