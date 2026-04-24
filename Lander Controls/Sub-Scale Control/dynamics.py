import numpy as np
#This Program Defines the Dynamics of the CPLC Sub-Scale Lander using Newton-Eular Equations

#Walking Through the Program
#26-34: Define globel variables and physcial lander properties and insert the inertia measurements into Inertia Matrix
#37-47: Function that converts Body Dynamics (Body being the Lander) to World Dynamics (What someone stationary watching the lander is seeing)
#       The inside of the function is not important so long as you understand that it converts from a Body frame to World frame
#50-95: 51-59: Define X-Matrix describing the position, velcity, angle and angular rate of the lander. Some parts are grouped for later use
#       62-65: Define U-Matrix describing the ability of the lander to change its dynamics. Thrust, Yaw due to motor torque and gimbal angle.
#              Rotation_Matrix_Body_to_World function is called to define R and define the landers angular dynamics
#       68-74: F_Thrust_Body: A matrix that describes how the lander reacts when forces are applied to (x,y,z)-Axis
#              F_Thrust_World: Matrix Multiplication of R (Convert to World) and F_Thrust_Body Matrix 
#              F_Gravity_World: Matrix describing how the force of gravity effects (x,y,z)-Axis
#              F_World: Adds both Gravity Force and Lander Force (From F_Thrust_World) to describe descibe the sub of forces in the system
#              Accel: Using Newton's 2nd Law the acceleration of the system can be found by dividing Total Force (F_World) by the Landers mass
#       77-86: Tau_body is the torque of the lander calculated by: Tau_X = -T*lengthCOM*sin(gimbal angle x),
#              Tau_Y = -T*lengthCOM*sin(gimbal angle y), Tau_Z = Tau_Z (Torque produced by spinning motors)
#              I_Matrix adds the inertia values for X,Y,Z into a diagonal matrix to be used in matrix multiplication
#              Omega_Dot (Anglular Acceleration) = (I_Matrix)^-1 * (Tau_Body - Gyroscope coupling term)
#              Theta_Dot = Omega defines the landers angular rate is the same as the world angular rate (Only works to +/- 15-20 degrees)
#       89-95: By using the variables commputed in above, the x_dot matrix (Derivative of X-Matrix) can be formed. This is the value that is
#              Returned by the nonlinear_dynamics function when given the landers current state (x) and the current inputs (u)   


#Physical Parameters
mass = 0.880 #kg
inertia_X = 0.017 #kg/m^2 #Mass moment of Inertia about X
inertia_Y = 0.017 #kg/m^2 #Mass moment of Inertia about Y
inertia_Z = 0.004 #kg/m^2 #Mass moment of Inertia about Z
lengthCOM = 0.077656 #m #Center of Mass to Gimbal Pivot Distance
gravity = -9.81 #m/s^2




def rotation_Matrix_Body_to_World(theta_x, theta_y, theta_z):
    cx, sx = np.cos(theta_x), np.sin(theta_x)
    cy, sy = np.cos(theta_y), np.sin(theta_y)
    cz, sz = np.cos(theta_z), np.sin(theta_z)

    R = np.array([
        [cy*cz, sx*sy*cz-cx*sz, cx*sy*cz+sx*sz],
        [cy*sz, sx*sy*sz+cx*cz, cx*sy*sz-sx*cz],
        [-sy, sx*cy, cx*cy]])

    return R


def nonlinear_dynamics(x, u):
    #Lander State Variables
    pos_x, pos_y, pos_z = x[0], x[1], x[2] #Position of x,y,z
    vel_x, vel_y, vel_z = x[3], x[4], x[5] #Velocity of x,y,z
    theta_x, theta_y, theta_z = x[6], x[7], x[8] #Attitude Angles
    omega_x, omega_y, omega_z = x[9], x[10], x[11] #Attitude Anglular Rates
    pos = x[0:3]
    vel = x[3:6]
    theta = x[6:9]
    omega = x[9:12]

    #Lander Input Variables (what does the motors and gimbals input into the system)
    thrust, alpha_x, alpha_y, tau_z = u[0], u[1], u[2], u[3]

    #Call rotation_Matrix_Body_to_World to define R
    R = rotation_Matrix_Body_to_World(theta_x, theta_y, theta_z)

    #Total Forces
    F_thrust_body = np.array([thrust*np.sin(alpha_x), thrust*np.sin(alpha_y), thrust*np.cos(alpha_x)*np.cos(alpha_y)])
    F_thrust_world = R @ F_thrust_body
    F_gravity_world = np.array([0, 0, mass*gravity]) 
    F_world = F_thrust_world + F_gravity_world

    #Total World Acceleration
    accel = F_world/mass

    #Torques acting on Body
    tau_body = np.array([-thrust*lengthCOM*np.sin(alpha_x), -thrust*lengthCOM*np.sin(alpha_y), tau_z])

    #Insert MMI into Diagonal Matrix
    I_matrix = np.diag([inertia_X, inertia_Y, inertia_Z])
    
    #Compute Body Torques by Matrix Multiplication
    omega_dot = np.linalg.inv(I_matrix) @ (tau_body - np.cross(omega, I_matrix @ omega))

    #Relate Lander Angular Rate to World frame angular rate
    theta_dot = omega

    #Compute the derivative of all values in x-Matrix and add them to new matrix x_dot
    x_dot = np.zeros(12)
    x_dot[0:3] = vel
    x_dot[3:6] = accel
    x_dot[6:9] = theta_dot
    x_dot[9:12] = omega_dot
    
    return x_dot


def linearized_dynamics():
    x_trim = np.zeros(12)
    u_trim = np.array([-mass*gravity, 0, 0, 0])

    step = 1e-6
    
    A_Matrix = np.zeros((12,12))
    B_Matrix = np.zeros((12,4))

    for i in range(12):
        x_trim_stepup = x_trim.copy()
        x_trim_stepup[i] += step

        x_trim_stepdown = x_trim.copy()
        x_trim_stepdown[i] -= step

        x_trim_up = nonlinear_dynamics(x_trim_stepup, u_trim)
        x_trim_down = nonlinear_dynamics(x_trim_stepdown, u_trim)

        A_Matrix[:, i] = (x_trim_up - x_trim_down) / (2*step)

    for j in range(4):
        u_trim_stepup = u_trim.copy()
        u_trim_stepup[j] += step

        u_trim_stepdown = u_trim.copy()
        u_trim_stepdown[j] -= step

        u_trim_up = nonlinear_dynamics(x_trim, u_trim_stepup)
        u_trim_down = nonlinear_dynamics(x_trim, u_trim_stepdown)
        
        B_Matrix[:, j] = (u_trim_up - u_trim_down) / (2*step)
    
    return A_Matrix, B_Matrix

