#import pigpio
import math
import time
from scipy.optimize import fsolve

servo_pin = 18
r_u = 0.85
h_u = 4.160360
r_l = 0.47
h_l = 2.302372

#pi = pigpio.pi()
#pi.set_mode(servo_pin, pigpio.OUTPUT)
'''
def angle_upper(angle):
    phi_rad_u = math.asin(r_u*math.sin(angle*math.pi/180)/math.sqrt(r_u**2 + h_u**2 - 2*r_u*h_u*math.cos(angle*math.pi/180)))
    phi_deg_u = phi_rad_u * 180/math.pi
    return phi_deg_u
    '''

def angle_upper(angle):
    phi_rad_u = math.sin(r_u*math.asin(angle*math.pi/180)/math.sqrt(r_u**2 + h_u**2 - 2*r_u*h_u*math.acos(angle*math.pi/180)))
    phi_deg_u = phi_rad_u * 180 / math.pi
    return phi_deg_u

def angle_lower(angle):
    phi_rad_l = math.asin(r_l*math.sin(angle*math.pi/180)/math.sqrt(r_l**2 + h_l**2 - 2*r_l*h_l*math.cos(angle*math.pi/180)))
    phi_deg_l = phi_rad_l * 180/math.pi
    return phi_deg_l

def set_angle(angle):
    angle = angle_upper(angle)
    print(angle)
    pulse_width = int(angle/180*2000 + 500)
    #pi.set_servo_pulsewidth(servo_pin, pulse_width)

try:
    angle = float(input("Enter a value between 135 to 45: "))
    #angle = angle - 90
    set_angle(angle)
    time.sleep(1)

except KeyboardInterrupt:
    pi.stop()