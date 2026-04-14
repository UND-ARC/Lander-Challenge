%Hardware Limits
gimbal_Max = deg2rad(15);
gimbal_Min = deg2rad(-15);
max_Thrust = 11.77;
min_Thrust = 0;

%Error Limits
x_max = 0.1;
y_max = 0.1;
z_max = 0.05; 
xprime_max = 0.005; 
yprime_max = 0.005;
zprime_max = 0.005;
thetaX_max = deg2rad(15);
thetaY_max = deg2rad(15);
thetaprimeX_max = deg2rad(.5);
thetaprimeY_max = deg2rad(.5);

%Input Max
thrust_Max = 11;
gimbalXY_Max = 10;


%Physical Values
m = 0.877; %Mass (kg)
L = 0.077656; %COM to Gimbal Pivot (m)
I_x = 0.017; %Mass Moment of Inertia about X-Axis (kg*m^2)
I_y = 0.017; %Mass Moment of Inertia about Y-Axis (kg*m^2)
g = 9.81; %Gravity (m/s^2)
T_0 = m * g; %Force of Gravity (N)


%Matrix A: State Space (no Input)
A = zeros(10,10);
A(1,4) = 1;
A(2,5) = 1;
A(3,6) = 1;
A(4,8) = g;
A(5,7) = -g;
A(6,3) = -g/T_0;
A(7,9) = 1;
A(8,10) = 1;


%Matrix B: Input Effects (Thrust, Gimbal-X, Gimbal-Y)
B = zeros(10,3);
B(6,1) = 1/m;
B(9,2) = T_0*L/I_x;
B(10,3) = T_0*L/I_y;


%Matrix C: Sensor Values 
C = eye(10,10); %Current Matrix Assumes Perfect Sensor Readings


%Matrix D: Feedthrough Matrix (Zeros-Takes time to change values)
D = zeros(10,3);


%Matrix Q: Error Multiplier (How much you care about an error value)
%Q = diag([.5, .5, 50, 1, 1, 1, 1, 1, 1, 1]);
Q = diag([1/x_max^2, 1/y_max^2, 1/z_max^2, 1/xprime_max^2, ...
          1/yprime_max^2, 1/zprime_max^2, 1/thetaX_max^2, ...
          1/thetaY_max^2, 1/thetaprimeX_max^2, 1/thetaprimeY_max^2]);

%Matrix R: Control Input Weight (How much fast you want error corrected)
%R = diag([1, 5, 5]);
R = diag([1/thrust_Max^2, 1/gimbalXY_Max^2, 1/gimbalXY_Max^2]);

%Matrix x0: Lander Starting Point
x0 = zeros(10,1);
x0(1) = 0.5;
x0(1) = 0.5;
x0(7) = deg2rad(2);
x0(8) = deg2rad(2);



%Matrix S: Setpoint Values for System
S = zeros(10,1);
S(3) = 4; %Z height to 4m


%Solve Controllablility and Eigen Values
Co = ctrb(A, B);
fprintf('Controllable rank: %d (need 10)\n', rank(Co))
[K, ~, CL_eigs] = lqr(A, B, Q, R);
fprintf('Closed-loop eigenvalues:\n')
disp(CL_eigs)


%SIMULINK and Graphing Code
simOut = sim('SIMULINK_Module');
x_out = simOut.x_out;
run('Plot_LQR_Results.m');




