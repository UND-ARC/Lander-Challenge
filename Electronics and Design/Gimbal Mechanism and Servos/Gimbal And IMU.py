import time
import math
import pickle
import pigpio
import numpy as np
from adafruit_extended_bus import ExtendedI2C as I2C
import adafruit_bno055
from simple_pid import PID

# To enable i2c-gpio, add the line `dtoverlay=i2c-gpio` to /boot/config.txt
# Then reboot the pi

# Create library object using our Extended Bus I2C port
# Use `ls /dev/i2c*` to find out what i2c devices are connected

i2c = I2C(1)                                                            # Device is /dev/i2c-1
sensor = adafruit_bno055.BNO055_I2C(i2c, 0x28)                          # Can add second IMU with address 0x29
sensor.mode = adafruit_bno055.IMUPLUS_MODE                               #changes mode from default (Doesn't work for vertical starting)

last_val = 0xFFFF

servo_pin1 = 14                                                         # Upper Gimbal (Pitch)
servo_pin2 = 15                                                         # Lower Gimbal (Yaw)
r_u = 0.85
h_u = 4.160360
r_l = 0.47
h_l = 2.302372
u = []
l = []

pi = pigpio.pi()
pi.set_mode(servo_pin1, pigpio.OUTPUT)
pi.set_mode(servo_pin2, pigpio.OUTPUT)

def load_calibration():
    try:
        with open("/home/ARC/Github ARC/Lander-Challenge/Electronics and Design/BNO055 IMU/calibration_data.pkl", "rb") as f:
            offsets = pickle.load(f)
            sensor.offsets_magnetometer = offsets[0]
            sensor.offsets_gyroscope = offsets[1]
            sensor.offsets_accelerometer = offsets[2]
        print("Calibration data loaded.")
    except FileNotFoundError:
        print("No calibration data found. Perform calibration first.")

def temperature():
    global last_val                                                     # Pylint: disable=global-statement
    result = sensor.temperature

    if abs(result - last_val) == 128:
        result = sensor.temperature
        if abs(result - last_val) == 128:
            return 0b00111111 & result

    last_val = result
    return result

def quartenion_to_euler(x, y, z, w):
    try:
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
    except:
        return(None, None, None)

def angle_upper(angle):     
    found = -45 + 90 + 1/900*min(range(len(u)), key = lambda i: abs(u[i]-angle)) # Finds closest index that contains the angle, then converts it
    return round(found, 2)                                              # Rounds to second decimal, as the rest is unneccesary

def angle_lower(angle):
    found = -45 + 90 + 1/900*min(range(len(l)), key = lambda i: abs(l[i]-angle)) # Finds closest index that contains the angle, then converts it
    return round(found, 2)                                              # Rounds to second decimal, as the rest is unneccesary

def set_angle(phi_upper, phi_lower):                                    # Controls servo motion
    angle1 = angle_upper(phi_upper)
    angle2 = angle_lower(phi_lower)
    pulse_width1 = int(angle1/180*2000 + 500)
    pi.set_servo_pulsewidth(servo_pin1, pulse_width1)
    pulse_width2 = int(angle2/180*2000 + 500)
    pi.set_servo_pulsewidth(servo_pin2, pulse_width2)

def main():
    num = 0
    #load_calibration()    #don't calibrate until rest is fixed
    while num < 5:                                                          # Getting sensor calibrated 
        quartenion = sensor.quaternion                                      # Getting data from IMU
        roll, pitch, yaw= quartenion_to_euler(quartenion[0], quartenion[1], quartenion[2], quartenion[3])
        time.sleep(0.1)
        num += 1
    rollControl = roll                                                      # Assigning start position
    #print(rollControl)
    print(yaw)
    #yawControl = yaw                                                        
    i = -45                                                                 # Uses Christian's formula to store angles in a list
    while (i <= 45):                 
        phi_rad_u = math.asin(r_u*math.sin(i*math.pi/180)/math.sqrt(r_u**2 + h_u**2 - 2*r_u*h_u*math.cos(i*math.pi/180)))
        phi_deg_u = phi_rad_u * 180/math.pi
        u.append(phi_deg_u)
        i = i + 1/900

    j = -45                                                                 # Uses Christian's formula to store angles in a list 
    while(j <= 45):
        phi_rad_l = math.asin(r_l*math.sin(j*math.pi/180)/math.sqrt(r_l**2 + h_l**2 - 2*r_l*h_l*math.cos(j*math.pi/180)))
        phi_deg_l = phi_rad_l * 180/math.pi
        l.append(phi_deg_l)
        j = j + 1/900
    
    pidPitch = PID(.75, 0.0, 0.0, setpoint = pitch)                         # Initializing the PID for Pitch control
    pidPitch.sample_time = .05

    #pidYaw = PID(0.25, 0.0, 0.0, setpoint = yaw/5)                            # Initializing the PID for Yaw control
    #pidYaw.sample_time = .05
    '''
    STARTING LOOP FOR ROCKET CONTROL
    '''
    try:
        while True:
            quartenion = sensor.quaternion                               # Getting data from IMU
            Roll, Pitch, Yaw = quartenion_to_euler(quartenion[0], quartenion[1], quartenion[2], quartenion[3])
            if(Roll != None or Pitch != None or Yaw != None):
                roll = Roll
                pitch = Pitch     
                yaw = Yaw                                                                             
            '''
            if (abs(roll) > abs(rollControl)):
                controlPitch = pidPitch(pitch)                              # Setting control for Pitch
            else:
                controlPitch = 0 - pidPitch(pitch)
            #controlYaw = pidYaw(yaw)
            
            if (yaw < yawControl):                                               # Determine relative distance from start
                controlYaw = pidYaw((yawControl + abs(yaw - yawControl)))
            elif(yaw < 0 and yaw > yawControl):
                controlYaw = 0 - pidYaw(yaw)                                 # Positive control for Yaw
            else:
                controlYaw = pidYaw(-yaw)                      # Negative control for Yaw'
            '''
            controlPitch = pidPitch(pitch)
            controlLower =  controlPitch * (math.cos(math.pi * (roll - rollControl) / 180))    # Accounting for relative position
            #controlYaw = pidYaw(yaw) * (math.sin(math.pi * (roll - rollControl + 90) / 180))       # Taken out due to funky motion        
            controlUpper = controlPitch * (math.sin(math.pi * (roll - rollControl) / 180))
            
            phi_lower = controlLower
            phi_upper = controlUpper
            set_angle(phi_upper, phi_lower)                             # Setting gimbal angle
            
            '''
            print("Pitch:", pitch)
            #print("Yaw:", yaw)
            #print("Upper Gimbal:", phi_upper)                           # Display gimbal angle
            #print("Lower Gimbal:", phi_lower)
            print('Roll:', roll)
            #print("Roll - Rollcontrol:", roll - rollControl)
            print()
            time.sleep(.5)
            '''
            
    except KeyboardInterrupt:
        pi.stop()

main()