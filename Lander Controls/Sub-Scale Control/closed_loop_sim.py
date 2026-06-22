import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from dynamics import nonlinear_dynamics, mass, gravity
from lander_control import saturate
from lander_control import LQRController

dt_control = 0.01 # Run Simulation at 100Hz
t_end = 10 # Run Simulation for 10 seconds

#Q Weighs How Important it is to correct an error in a State (Higher the number the more important it is)
Q = np.diag([10, 10, 10,        # X-Position | Y-Position | Z-Position
             10, 10, 500,        # X-Velocity | Y-Velocity | Z-Velocity
              1,  1,  1,        # Pitch      | Roll       | Yaw
             .5, .5, .5])       # Pitch Rate | Roll Rate  | Yaw Rate

# R Weighs How Expensive it is to use the input (Higher the number the more expensive it is)
R = np.diag([10, 4, 4, 1 ])    #Thrust      | Gimbal-X   | Gimbal-Y   | Torque-Z 



controller = LQRController(Q, R)
print(controller.K.shape)
print(controller.u_trim)

x_current = np.zeros(12)
x_target = np.zeros(12)

# Target State Matrix Values
# x_target[0] = 0 # X-Position (m)
# x_target[1] = 0 # Y-Position (m)
x_target[2] = 4 # Z-Position (m)
# x_target[3] = 0 # X-Velocity (m/s)
# x_target[4] = 0 # Y-Velocity (m/s)
# x_target[5] = 0 # Z-Velocity (m/s)

# x_target[6] = np.radians(0) # Roll (rad)
# x_target[7] = np.radians(0) # Pitch (rad)
# x_target[8] = np.radians(0) # Yaw (rad)

# x_target[9] = np.radians(0) # Roll Rate (rad/s)
# x_target[10] = np.radians(0) # Pitch Rate (rad/s)
# x_target[11] = np.radians(0) # Yaw Rate (rad/s)


# Current State Matrix Values (Note all values assumed to be zero unless specified)
# x_current[0] = 0 # X-Position (m)
# x_current[1] = 0 # Y-Position (m)
# x_current[2] = 0 # Z-Position (m)

# x_current[3] = 0 # X-Velocity (m/s)
# x_current[4] = 0 # Y-Velocity (m/s)
# x_current[5] = 0 # Z-Velocity (m/s)

x_current[6] = np.radians(3) # Roll (rad)
# x_current[7] = np.radians(0) # Pitch (rad)
# x_current[8] = np.radians(0) # Yaw (rad)

# x_current[9] = np.radians(0) # Roll Rate (rad/s)
# x_current[10] = np.radians(0) # Pitch Rate (rad/s)
# x_current[11] = np.radians(0) # Yaw Rate (rad/s)

t = 0
x = x_current.copy()
t_history = []
x_history = []
u_history = []

while t <= t_end:
    u_raw = controller.compute(x, x_target)
    u = saturate(u_raw)

    t_history.append(t); x_history.append(x.copy()); u_history.append(u.copy())

    sol = solve_ivp(lambda t, x: nonlinear_dynamics(x, u), [t, t + dt_control], x)
    x = sol.y[:, -1]

    if x[2] < 0:
        x[2] = 0
        x[5] = 0

    t += dt_control

x_history = np.array(x_history)

print(x_history[-1])


t_history = np.array(t_history)
u_history = np.array(u_history)




# Graph Position, Velocity, and Acceleration (X, Y, Z)
ax = np.gradient(x_history[:, 3], t_history)
ay = np.gradient(x_history[:, 4], t_history)
az = np.gradient(x_history[:, 5], t_history)
fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
axes[0].plot(t_history, x_history[:, 0], label='X')
axes[0].plot(t_history, x_history[:, 1], label='Y')
axes[0].plot(t_history, x_history[:, 2], label='Z')
axes[0].set_ylabel('Position (m)')
axes[0].legend()
axes[0].grid(True)
axes[1].plot(t_history, x_history[:, 3], label='Vx')
axes[1].plot(t_history, x_history[:, 4], label='Vy')
axes[1].plot(t_history, x_history[:, 5], label='Vz')
axes[1].set_ylabel('Velocity (m/s)')
axes[1].legend()
axes[1].grid(True)
axes[2].plot(t_history, ax, label='Ax')
axes[2].plot(t_history, ay, label='Ay')
axes[2].plot(t_history, az, label='Az')
axes[2].set_ylabel('Acceleration (m/s²)')
axes[2].set_xlabel('Time (s)')
axes[2].legend()
axes[2].grid(True)
plt.tight_layout()
plt.show()


# Graph Angle and Anglular Rate (Yaw, Pitch and Roll)
fig2, axes2 = plt.subplots(4, 1, figsize=(10, 10), sharex=True)
axes2[0].plot(t_history, u_history[:, 0], label='Thrust')
axes2[0].set_ylabel('Thrust (N)')
axes2[0].legend()
axes2[0].grid(True)
axes2[1].plot(t_history, np.degrees(u_history[:, 1]), label='Gimbal Roll Rate')
axes2[1].set_ylabel('Gimbal Roll Rate (deg/s)')
axes2[1].legend()
axes2[1].grid(True)
axes2[2].plot(t_history, np.degrees(u_history[:, 2]), label='Gimbal Pitch Rate')
axes2[2].set_ylabel('Gimbal Pitch Rate (deg/s)')
axes2[2].legend()
axes2[2].grid(True)
axes2[3].plot(t_history, u_history[:, 3], label='Yaw Torque')
axes2[3].set_ylabel('Yaw Torque (N·m)')
axes2[3].set_xlabel('Time (s)')
axes2[3].legend()
axes2[3].grid(True)
plt.tight_layout()
plt.show()


#Graph Gimbal and Thrust Saturation
fig2, axes2 = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
axes2[0].plot(t_history, u_history[:, 0], label='Thrust')
axes2[0].axhline(11.77, color='r', linestyle='--', alpha=0.5, label='Saturation')
axes2[0].axhline(0, color='r', linestyle='--', alpha=0.5)
axes2[0].set_ylabel('Thrust (N)')
axes2[0].legend(); axes2[0].grid(True)
axes2[1].plot(t_history, np.degrees(u_history[:, 1]), label='Gimbal X')
axes2[1].plot(t_history, np.degrees(u_history[:, 2]), label='Gimbal Y')
axes2[1].axhline(10, color='r', linestyle='--', alpha=0.5, label='Saturation')
axes2[1].axhline(-10, color='r', linestyle='--', alpha=0.5)
axes2[1].set_ylabel('Gimbal Angle (deg)')
axes2[1].set_xlabel('Time (s)')
axes2[1].legend(); axes2[1].grid(True)
plt.tight_layout()
plt.show()