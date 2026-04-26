import numpy as np
from scipy.linalg import solve_continuous_are
from dynamics import linearized_dynamics, mass, gravity

# This Program Takes values from dynamics.py and creates an LQR with computed K values. The program takes in dynamics.py A and B matrices
# Along with lander_control.py user entered

thrust_min = 0 
thrust_max = 11.77
gimbal_max = np.radians(10)
yaw_max = 0.05

def saturate(u):
    u_sat = np.zeros(4)
    u_sat[0] = np.clip(u[0], thrust_min, thrust_max)
    u_sat[1] = np.clip(u[1], -gimbal_max, gimbal_max)
    u_sat[2] = np.clip(u[2], -gimbal_max, gimbal_max)
    u_sat[3] = np.clip(u[3], -yaw_max, yaw_max)
    return u_sat

class LQRController:
    def __init__(self, Q, R):
        A, B = linearized_dynamics()
        P = solve_continuous_are(A, B, Q, R)
        self.K = np.linalg.inv(R) @ B.T @ P
        self.u_trim = np.array([-mass*gravity, 0, 0, 0])

    def compute(self, x_current, x_target):
        x_error = x_current - x_target
        return self.u_trim - self.K @ x_error


#Insert Q and R values and simulate their effect on K values and the Eigen Values of the system
if __name__ == "__main__":
    # Simple starting Q and R
    Q = np.diag([10, 10, 10,   # position
                 10, 10, 10,   # velocity
                 1, 1, 1,      # attitude
                 .5, .5, .5])     # angular rate
    R = np.diag([.5, 2, 2, 50])
    
    controller = LQRController(Q, R)
    
    print("K shape:", controller.K.shape)   # expect (4, 12)
    print("K matrix:")
    print(np.round(controller.K, 3))
    
    # Check closed-loop stability
    from dynamics import linearized_dynamics
    A, B = linearized_dynamics()
    eigenvalues = np.linalg.eigvals(A - B @ controller.K)
    print("Closed-loop eigenvalues:")
    print(np.round(eigenvalues, 3))
    print("=" * 50)

    #Make the Output Look Pretty
    print("Q weights (diagonal):")
    state_names = ['x', 'y', 'z', 'vx', 'vy', 'vz',
                   'θx', 'θy', 'θz', 'ωx', 'ωy', 'ωz']
    for name, q in zip(state_names, np.diag(Q)):
        print(f"  {name:>4}: {q:>8.2f}")

    print("\nR weights (diagonal):")
    input_names = ['T', 'αx', 'αy', 'τz']
    for name, r in zip(input_names, np.diag(R)):
        print(f"  {name:>4}: {r:>8.2f}")

    print("\nClosed-loop eigenvalues (sorted by speed):")
    eigs = np.linalg.eigvals(A - B @ controller.K)
    eigs_sorted = sorted(eigs, key=lambda e: -abs(e.real))  # fastest first
    for e in eigs_sorted:
        if abs(e.imag) < 1e-6:
            print(f"  {e.real:>8.2f}       (time constant: {1/abs(e.real):.3f} s)")
        else:
            print(f"  {e.real:>8.2f} ± {abs(e.imag):.2f}j  (damped osc)")