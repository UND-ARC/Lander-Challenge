#import pigpio
import math
import time

servo_pin = 18
r_u = 0.85
h_u = 4.160360
r_l = 0.47
h_l = 2.302372
u = []
l = []

i = -45
while (i <= 45):
    phi_rad_u = math.asin(r_u*math.sin(i*math.pi/180)/math.sqrt(r_u**2 + h_u**2 - 2*r_u*h_u*math.cos(i*math.pi/180)))
    phi_deg_u = phi_rad_u * 180/math.pi
    u.append(phi_deg_u)
    i = i + 1/900

j = -45
while(j <= 45):
    phi_rad_l = math.asin(r_l*math.sin(j*math.pi/180)/math.sqrt(r_l**2 + h_l**2 - 2*r_l*h_l*math.cos(j*math.pi/180)))
    phi_deg_l = phi_rad_l * 180/math.pi
    l.append(phi_deg_l)
    j = j + 1/900

#pi = pigpio.pi()
#pi.set_mode(servo_pin, pigpio.OUTPUT)

def angle_upper(angle):
    found = -45 + 1/900*min(range(len(u)), key = lambda i: abs(u[i]-angle))
    return round(found, 2)

def angle_lower(angle):
    found = -45 + 1/900*min(range(len(l)), key = lambda i: abs(l[i]-angle))
    return round(found, 2)

def set_angle(phi_upper, phi_lower):
    angle1 = angle_upper(phi_upper)
    angle2 = angle_lower(phi_lower)
    print("The upper angle is:", angle1)
    print("The lower angle is:", angle2)
    #pulse_width = int(angle1/180*2000 + 500)
    #pi.set_servo_pulsewidth(servo_pin, pulse_width)

try:
    phi_upper = float(input("Enter a value between 9.58 to -9.58 for the upper servo: "))
    phi_lower = float(input("Enter a value between 9.58 to -9.58 for the lower servo: "))
    set_angle(phi_upper, phi_lower)
    time.sleep(1)

except KeyboardInterrupt:
    pi.stop()