#import pigpio
import math
import time

servo_pin = 18
r_u = 0.85
h_u = 4.160360
r_l = 0.47
h_l = 2.302372
u = {}
l = {}

i = -45
while (i <= 45):
    phi_rad_u = math.asin(r_u*math.sin(i*math.pi/180)/math.sqrt(r_u**2 + h_u**2 - 2*r_u*h_u*math.cos(i*math.pi/180)))
    phi_deg_u = phi_rad_u * 180/math.pi
    u[round(phi_deg_u, 2)] = i
    i = i + 0.01

j = -45
while(j <= 45):
    phi_rad_l = math.asin(r_l*math.sin(i*math.pi/180)/math.sqrt(r_l**2 + h_l**2 - 2*r_l*h_l*math.cos(i*math.pi/180)))
    phi_deg_l = phi_rad_l * 180/math.pi
    l[round(phi_deg_l, 2)] = j
    j = j + 0.01

#pi = pigpio.pi()
#pi.set_mode(servo_pin, pigpio.OUTPUT)

def angle_upper(angle):
    return u[round(angle, 2)]

def angle_lower(angle):
    return l[round(angle, 2)]

def set_angle(angle):
    angle = angle_upper(angle)
    print(angle)
    pulse_width = int(angle/180*2000 + 500)
    #pi.set_servo_pulsewidth(servo_pin, pulse_width)

try:
    phi = float(input("Enter a value between 135 to 45: "))
    #angle = angle - 90
    set_angle(phi)
    time.sleep(1)

except KeyboardInterrupt:
    pi.stop()