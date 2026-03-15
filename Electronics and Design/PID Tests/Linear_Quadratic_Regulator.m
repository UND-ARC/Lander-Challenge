% The Linear Quadratic Regulator will calculate the rockets angular velocity
% and angular acceleration using an LQR. By turning the second order diff
% equation into two first order diff equations matrixes are able to be
% formed to compute these two values from the LQR equation.



%% Part 1 - Input data about the rockets physical properties
mass  = 0.5;      % kg    total rocket mass
Iy    = 0.05;     % kg·m² moment of inertia about pitch axis
T     = 10.0;     % N     thrust (average from your motor thrust curve)
L_arm = 0.30;     % m     distance from nozzle pivot to center of mass
Ma    = 2.0;      % s⁻²  aerodynamic pitching moment derivative



%% Part 2 - Computes how Torque and corrections will effect the rocket
% System matrix — encodes rocket's natural (uncontrolled) dynamics
A = [0,   1;
     Ma,  0];

% Input matrix — encodes how gimbal deflection affects the rocket
B = [0;
     T * L_arm / Iy];

% Output matrix — Values the IMU is actually reading. No modification is
% needed to them since the IMU reads both angular and pitch rate
C = eye(2);       % Eye = 2x2 identity matrix

% Feedthrough matrix — Zeros because the feedback in the system is not
% instantanous
D = zeros(2, 1);

% Print A-D Matrix
fprintf('A matrix:\n');  disp(A)
fprintf('B matrix:\n');  disp(B)
fprintf('C matrix:\n');  disp(C)
fprintf('D matrix:\n');  disp(D)



%% Part 3 - Compute the Rockets Eigenvalues (How unstable the rocket is)

OL_eigenvalues = eig(A);
fprintf('Open-loop eigenvalues: %.4f  and  %.4f\n', ...
        OL_eigenvalues(1), OL_eigenvalues(2))

% Interpretations:
%   Negative real part = stable mode (naturally decays)
%   Positive real part = unstable mode (naturally grows)
%   One positive & One Negative = rocket will tip over without control



%% Part 5 - LQR Design
% Groups variables A-D into a system since they are all related to
% eachother. ss commands this operation
sys = ss(A, B, C, D);

% Choose Q — How much the system should care about changing X1 and X2
% values compared to eachother. Is one more costly than the other?
% Q for X1 = Q(1,1) Q value for Pitch Rate
% Q for X2 = Q(2,2) Q value for Angular Rate
Q = diag([10, 1]); %Pitch Rate is 10x more important than Angular Rate)


% Choose R — How hard the gimbal will work to correct error
% Larger R = gentler gimbal movement
% Smaller R = more aggressive gimbal movement
R = 0.1;

% Solve the Riccati equation and compute optimal K
% All values should be negative, otherwise the system is still unstable
% k1 is for angular rate. k2 is for pitch angle
[K, P, CL_eigenvalues] = lqr(sys, Q, R);
fprintf('\nOptimal gain matrix K = [k1, k2]:\n');
disp(K)

fprintf('Closed-loop eigenvalues:\n');
disp(CL_eigenvalues)



%% Part 6 - Graph of Found Values and Their Effects

% Build the closed loop system
% Control law is u = -Kx, substituting into ẋ = Ax + Bu gives:
% ẋ = Ax + B(-Kx) = (A - BK)x
A_cl = A - B * K;
sys_cl = ss(A_cl, B, C, D);

% Initial conditions — rocket starts slightly tilted
% Matches the paper's starting condition
x0 = [0.05;   % theta_0     = 0.05 rad (~3 degrees)
      0.00];  % theta_dot_0 = 0 rad/s (not yet rotating)

% Time vector — simulate 5 seconds at 1ms resolution
t = 0 : 0.001 : 5;

% Simulate initial condition response
% initial() gives the unforced response from x0
[y, t_out] = initial(sys_cl, x0, t);

figure('Name', 'LQR TVC Response', 'NumberTitle', 'off')

% Plot 1 — Pitch angle
subplot(3, 1, 1)
plot(t_out, y(:,1), 'b', 'LineWidth', 2)
yline(0, 'k--', 'LineWidth', 1)         
xlabel('Time (s)')
ylabel('Pitch Angle (rad)')
title('Pitch Angle — LQR Response')
grid on

% Plot 2 — Angular rate
subplot(3, 1, 2)
plot(t_out, y(:,2), 'r', 'LineWidth', 2)
yline(0, 'k--', 'LineWidth', 1)
xlabel('Time (s)')
ylabel('Angular Rate (rad/s)')
title('Angular Rate')
grid on

% Plot 3 — Gimbal command (control effort)
% Reconstruct u = -Kx at each timestep
u_history = zeros(length(t_out), 1);
for i = 1:length(t_out)
    u_history(i) = -K * y(i,:)';
end

subplot(3, 1, 3)
plot(t_out, rad2deg(u_history), 'g', 'LineWidth', 2)
yline(0, 'k--', 'LineWidth', 1)
xlabel('Time (s)')
ylabel('Gimbal Angle (deg)')
title('Gimbal Command (Control Effort)')
grid on



%% Part 7 - Change R values for better visualization
% Test three different R values with Q fixed
Q_fixed = diag([10, 1]);
R_test  = [10.0,  0.1,  0.001];
colors  = {'r',  'b',  'g'};
labels  = {'R = 10.0 (gentle)', 'R = 0.1 (default)', 'R = 0.001 (aggressive)'};

figure('Name', 'Effect of R on Response')
hold on

for i = 1:3
    [K_i, ~, ~]  = lqr(sys, Q_fixed, R_test(i));
    A_cl_i       = A - B * K_i;
    sys_cl_i     = ss(A_cl_i, B, C, D);
    [y_i, t_i]   = initial(sys_cl_i, x0, t);
    
    plot(t_i, y_i(:,1), colors{i}, 'LineWidth', 2, 'DisplayName', labels{i})
    
    fprintf('R = %.2f  →  K = [%.4f,  %.4f]\n', R_test(i), K_i(1), K_i(2))
end

yline(0, 'k--')
xlabel('Time (s)')
ylabel('Pitch Angle (rad)')
title('Pitch Angle Response — Varying R (Q fixed)')
legend('Location', 'northeast')
grid on



%% Part 8 - Ensure controler has ≥ 6 dB of gain and phase margin ≥ 60°

% Compute gain and phase margins of the closed loop system
% margin() requires the open loop transfer function
sys_ol = ss(A, B, C, D);            % open loop plant
% Extract only the pitch angle output (row 1) for SISO margin analysis
sys_siso = sys_ol(1, :);
[Gm, Pm, Wcg, Wcp] = margin(sys_siso * tf(K(1,:), 1));

fprintf('\nGain  margin: %.2f dB  at  %.4f rad/s\n', 20*log10(Gm), Wcg)
fprintf('Phase margin: %.2f deg  at  %.4f rad/s\n', Pm, Wcp)

