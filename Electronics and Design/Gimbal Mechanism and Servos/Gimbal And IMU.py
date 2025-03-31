import time
import math
import pigpio
import numpy as np
from adafruit_extended_bus import ExtendedI2C as I2C
import adafruit_bno055
from simple_pid import PID

# To enable i2c-gpio, add the line `dtoverlay=i2c-gpio` to /boot/config.txt
# Then reboot the pi

# Create library object using our Extended Bus I2C port
# Use `ls /dev/i2c*` to find out what i2c devices are connected

i2c = I2C(1)  # Device is /dev/i2c-1
sensor = adafruit_bno055.BNO055_I2C(i2c, 0x28)  #can add second IMU with address 0x29

last_val = 0xFFFF

servo_pin1 = 14
servo_pin2 = 15
r_u = 0.85
h_u = 4.160360
r_l = 0.47
h_l = 2.302372
u = []
l = []

pi = pigpio.pi()
pi.set_mode(servo_pin1, pigpio.OUTPUT)
pi.set_mode(servo_pin2, pigpio.OUTPUT)

def temperature():
    global last_val  # pylint: disable=global-statement
    result = sensor.temperature

    if abs(result - last_val) == 128:
        result = sensor.temperature
        if abs(result - last_val) == 128:
            return 0b00111111 & result

    last_val = result
    return result

def quartenion_to_euler(x, y, z, w):
    t0 = +2.0*(w*x + y*z)
    t1 = +1.0 - 2.0*(x*x + y*y)
    roll_x = math.atan2(t0, t1)

    t2 = +2.0*(w*y - z*x)
    t2 = +1.0 if t2 > +1.0 else t2
    t2 = -1.0 if t2 < -1.0 else t2
    pitch_y = math.asin(t2)

    t3 = +2.0*(w*z + x*y)
    t4 = +1.0 - 2.0*(y*y + z*z)
    yaw_z = math.atan2(t3, t4)

    return roll_x*180/math.pi, pitch_y*180/math.pi, yaw_z*180/math.pi

def angle_upper(angle):     
    found = -45 + 90 + 1/900*min(range(len(u)), key = lambda i: abs(u[i]-angle)) #finds closest index that contains the angle, then converts it
    return round(found, 2)  #rounds to second decimal, as the rest is unneccesary

def angle_lower(angle):
    found = -45 + 90 + 1/900*min(range(len(l)), key = lambda i: abs(l[i]-angle)) #finds closest index that contains the angle, then converts it
    return round(found, 2)  #rounds to second decimal, as the rest is unneccesary

def set_angle(phi_upper, phi_lower):    #controls servo motion
    angle1 = angle_upper(phi_upper)
    angle2 = angle_lower(phi_lower)
    pulse_width1 = int(angle1/180*2000 + 500)
    pi.set_servo_pulsewidth(servo_pin1, pulse_width1)
    pulse_width2 = int(angle2/180*2000 + 500)
    pi.set_servo_pulsewidth(servo_pin2, pulse_width2)

def main():
    i = -45             #uses Christian's formula to store angles in a list
    while (i <= 45):                 
        phi_rad_u = math.asin(r_u*math.sin(i*math.pi/180)/math.sqrt(r_u**2 + h_u**2 - 2*r_u*h_u*math.cos(i*math.pi/180)))
        phi_deg_u = phi_rad_u * 180/math.pi
        u.append(phi_deg_u)
        i = i + 1/900

    j = -45             #uses Christian's formula to store angles in a list 
    while(j <= 45):
        phi_rad_l = math.asin(r_l*math.sin(j*math.pi/180)/math.sqrt(r_l**2 + h_l**2 - 2*r_l*h_l*math.cos(j*math.pi/180)))
        phi_deg_l = phi_rad_l * 180/math.pi
        l.append(phi_deg_l)
        j = j + 1/900

    pidPitch = PID(0.5, 0.0, 0.0, setpoint = -8.74)                    #initializing the PID for Pitch control
    pidPitch.sample_time = .25

    pidYaw = PID(0.1, 0.0, 0.0, setpoint = 178.08)                    #initializing the PID for Yaw control
    pidYaw.sample_time = .25

    try:
        while True:
            quartenion = sensor.quaternion
            roll, pitch, yaw= quartenion_to_euler(quartenion[0], quartenion[1], quartenion[2], quartenion[3])
            
            controlPitch = pidPitch(pitch)
            if (yaw < 0):
                controlYaw = pidYaw(yaw)
            else:
                controlYaw = 0 - pidYaw(abs(yaw))
            
            phi_upper = controlPitch
            phi_lower = controlYaw
            set_angle(phi_upper, phi_lower)

            print("Upper Gimbal:", phi_upper)
            print("Lower Gimbal:", phi_lower)
            time.sleep(.25)
    
    except KeyboardInterrupt:
        pi.stop()

main()