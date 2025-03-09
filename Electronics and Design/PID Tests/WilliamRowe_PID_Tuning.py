'''
University of North Dakota Collegiate Propulsive Lander Challenge (CPLC) Simulation
Written and Tested by: William Rowe

The main purpose of this code is to simulate a rocket flight given specified parameters.
'''
import math
import time
import matplotlib.pyplot as plt                                               #Graph Function
from mpl_toolkits import mplot3d                                              #3d Graph
from simple_pid import PID                                                    #PID Controls

#Static Global Values
CLOCK = 0.100                                                                 #How many ticks per second
fuelRange = 30                                                                #How long the rocket can be in the air
g = -9.81                                                                     #Gravity Constant

def forces(speed, thrust, angleX, angleY, windX, windY):                      #Function for setting speeds (Change for sensors when implamenting)
    z = (thrust * math.cos(angleX) * math.cos(angleY) + g) * CLOCK            #Z = (engine power * cos(engine gimbal in X) * cos(engine gimbal in Y) - 9.81) * CLOCK to get velocity
    x = (math.sin(angleX) * thrust - windX) * CLOCK                           #X = (engine power * sin(engine gimbal in X) - Acceleration from wind) * CLOCK to get velocity
    y = (math.sin(angleY) * thrust - windY) * CLOCK                           #Y = (engine power * sin(engine gimbal in Y) - Acceleration from wind) * CLOCK to get velocity
    speed[0] = speed[0] + x
    speed[1] = speed[1] + y
    speed[2] = speed[2] + z
    return(speed)

def angles(maxAngle, control):                                                #Function for setting angle & preventing overshoot
    angle = math.radians(maxAngle * control)
    if angle > maxAngle:
        angle = maxAngle
    elif angle < -maxAngle:
        angle = -maxAngle
    return(angle)
        
def thrustCalc(maxThrust, controlX, controlY, controlZ):                      #Setting thrust and ensuring it does not go above max thrust or below zero
    thrust = (maxThrust * (controlZ + abs(controlX/7) + abs(controlY/7))) - g 
    if thrust > maxThrust:
        thrust = maxThrust
    elif thrust < 1:
        thrust = 1
    return(thrust)

def main():
    print("Launch in 3")
    time.sleep(1)
    print("          2")
    time.sleep(1)
    print("          1")
    time.sleep(1)
    print("Lift off!\n")
    position = [0.0, 0.0, 0.0]      #Initial launch position
    xValues = []                    #Holder of X-Values for the graph
    yValues = []                    #Holder of Y-Values for the graph
    zValues = []                    #Holder of Z-Values for the graph
    times = []                      #Holder of t-Values for graphing
    thrusts = []                    #Holder of thrust Values for graphing
    t = 0
    checkpoints = 25                #How many checkpoints in descent phase
    target = [10.0, 10.0, 0.0]      #Target landing zone
    targetHeight = 50               #How high the rocket has to go before descent
    tolerance = 1                   #+/- how many meters from target height counts as hovering
    diam = 5.0                      #Diameter of landing circle
    maxAngle = math.radians(15)     #Maximum angle of gimbal
    maxThrust = 50
    speed = [0.0, 0.0, 0.0]         #Initializing speed list
    windX = 0.0                     #Wind interferance in X plane
    windY = 0.0                     #Wind interferance in Y plane
    angleX = 0
    angleY = 0
    
    pidX = PID(.4, 0.025, 1, setpoint = 0)                    #initializing the PID for horizontal control in the X-plane
    pidX.sample_time = CLOCK
    
    pidY = PID(.4, 0.025, 1, setpoint = 0)                    #initializing the PID for horizontal control in the Y-plane
    pidY.sample_time = CLOCK
    
    pidZ = PID(.02, 0.001, 0.014, setpoint = targetHeight)    #initializing the PID for vertical control
    pidZ.sample_time = CLOCK
    
    xValues.append(position[0])
    yValues.append(position[1])
    zValues.append(position[2])
    times.append(t)
    thrusts.append(0)
    hover = 0
    thrust = 0
    while (hover <= 3) & (t < fuelRange):
        controlX = pidX(position[0] + (speed[0] + windX) * CLOCK)
        controlY = pidY(position[1] + (speed[1] + windY) * CLOCK)
        controlZ = pidZ(position[2] + (speed[2]) * CLOCK)
        
        angleX = angles(maxAngle, controlX)                                   #Setting angleX and ensuring it does not go above max angle or below negative max angle
            
        angleY = angles(maxAngle, controlY)                                   #Setting angleY and ensuring it does not go above max angle or below negative max angle
            
        thrust = thrustCalc(maxThrust, controlX, controlY, controlZ)          #Setting thrust and ensuring it does not go above max thrust or below zero
          
        speed = forces(speed, thrust, angleX, angleY, windX, windY)        
        for x in range(3):
            position[x] = position[x] + speed[x]
        t = t + CLOCK        
        time.sleep(CLOCK)
        
        if (position[2] < (targetHeight + tolerance)) & (position[2] > (targetHeight - tolerance)):
            hover = hover + CLOCK
        else:
            hover = 0
        
        if ((t // CLOCK) % 1 == 0):
            xValues.append(position[0])
            yValues.append(position[1])
            zValues.append(position[2])
            times.append(t)
            thrusts.append(thrust)

    print("Launch Stage Completed")
    print(f"Time: {t: .2f}\n")
    
    if (t < fuelRange):                                                                             #Changing PID target to be landing circle
        number = 1
        while number <= checkpoints + 1:
            pidX = PID(.4, 0.0025, 1.75, setpoint = (target[0] * (number + 3) / checkpoints))       #initializing the PID for horizontal control in the X-plane
            
            pidY = PID(.4, 0.0025, 1.75, setpoint = (target[1] * (number + 3) / checkpoints))       #initializing the PID for horizontal control in the Y-plane
            
            pidZ = PID(.02, 0.015, 0.029, setpoint = (50 - 50 * (number + 1) / (checkpoints + 2)))
            
            hover = 0
            while not((position[0] <= (target[0] * number / checkpoints)) & (position[1] <= (target[1] * number / checkpoints)) & (position[2] < (55 - 50 * number / checkpoints))):
                    if (t > fuelRange):
                        break
                    controlX = pidX(position[0] + (speed[0] + windX) * CLOCK)
                    controlY = pidY(position[1] + (speed[1] + windY) * CLOCK)
                    controlZ = pidZ(position[2] + (speed[2]) * CLOCK)
                    
                    angleX = angles(maxAngle, controlX)                                       #Setting angleX
                        
                    angleY = angles(maxAngle, controlY)                                       #Setting angleY
                        
                    thrust = thrustCalc(maxThrust, controlX/2, controlY/2, controlZ/2)        #Setting thrust and ensuring it does not go above max thrust or below zero
                        
                    speed = forces(speed, thrust, angleX, angleY, windX, windY)        
                    for x in range(3):
                        position[x] = position[x] + speed[x]
                    t = t + CLOCK        
                    time.sleep(CLOCK)
                    
                    if (position[2] < (5 + tolerance)) & (position[2] > (5 - tolerance)):
                        hover = hover + CLOCK
                    else:
                        hover = 0                
                    
                    if ((t // CLOCK) % 1 == 0):

                        xValues.append(position[0])
                        yValues.append(position[1])
                        zValues.append(position[2])
                        times.append(t)
                        thrusts.append(thrust)
                    
                    if position[2] < 0:
                        break
            number = number + 1
    print("Descent Phase Completed")
    print(f"Time: {t: .2f}\n")    
        
    if (t < fuelRange):                                                               #Final landing approach
        pidZ = PID(.024, 0.002, 0.014, setpoint = 0)
        while ((position[2] > 0) & (t < fuelRange)):
            controlX = pidX(position[0] + (speed[0] + windX) * CLOCK)
            controlY = pidY(position[1] + (speed[1] + windY) * CLOCK)
            controlZ = pidZ(position[2] + (speed[2]) * CLOCK)
        
            angleX = angles(maxAngle, controlX)                                       #Setting angleX
        
            angleY = angles(maxAngle, controlY)                                       #Setting angleY
            if angleY > maxAngle:
                angleY = maxAngle
            elif angleY < -maxAngle:
                angleY = -maxAngle
        
            thrust = thrustCalc(maxThrust, controlX, controlY, controlZ)              #Setting thrust and ensuring it does not go above max thrust or below zero
            
            speed = forces(speed, thrust, angleX, angleY, windX, windY)        
            for x in range(3):
                position[x] = position[x] + speed[x]
            t = t + CLOCK        
            time.sleep(CLOCK)
            
            
            if ((t // CLOCK) % 1 == 0):
                xValues.append(position[0])
                yValues.append(position[1])
                zValues.append(position[2])
                times.append(t)
                thrusts.append(thrust)
                
            if position[2] < 0:
                break
            
    #Displaying Final Landing Data
    print("Final Landing Completed")    
    print(f"Time: {t: .01f}")
    print(f"Speed: ({speed[0]: .3f}, {speed[1]: .3f}, {speed[2]: .3f})")
    print(f"Position: ({position[0]: .3f}, {position[1]: .3f}, {position[2]: .3f})")
    
    #Creating Graphs
    fig1 = plt.figure()
    ax = plt.axes(projection = '3d')
    ax.plot3D(xValues, yValues, zValues, 'red')
    ax.set_title('Rocket Flight Path')
    
    fig2 = plt.figure()
    plt.plot(times, zValues, 'blue')
    plt.xlabel('Time(seconds)')
    plt.ylabel('Height(meters)')
    plt.title('Height Vs Time')
    
    fig3 = plt.figure()
    plt.plot(times, thrusts, 'orange')
    plt.title('Thrust Vs Time')
    plt.xlabel('Time(seconds)')
    plt.ylabel('Thrust(meters/s/s)')
    
    #Displaying Graphs
    plt.show()
    
    
main()
