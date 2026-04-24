import numpy as np
from scipy.linalg import solve_continuous_are
from dynamics import linearized_dynamics, mass, gravity

class LQRController:
    def _init_(self, Q, R):
        A, B = linearized_dynamics
        P = solve_continuous_are(A, B, Q, R)
        self.K = np.linalg.inv(R) @ B.T @ P