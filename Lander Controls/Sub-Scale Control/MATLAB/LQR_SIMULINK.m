%Hardware Limits
gimbal_Max = deg2rad(15);
gimbal_Min = deg2rad(-15);
max_Thrust = 11.77;
min_Thrust = 0;
thrust_Response = 1; %Thrust Response Time (1 second)
servo_Response = 0.30; %Servo Response Time (0.30 seconds)

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
A = zeros(13,13);
A(1,4) = 1;
A(2,5) = 1;
A(3,6) = 1;
A(4,8) = g;
A(5,7) = g;
A(6,11) = 1/m;
A(9,12) = T_0*L/I_x;
A(10,13) = T_0*L/I_y;
A(7,9) = 1;
A(8,10) = 1;
A(11,11) = -1/thrust_Response;
A(12,12) = -1/servo_Response;
A(13,13) = -1/servo_Response;


%Matrix B: Input Effects (Thrust, Gimbal-X, Gimbal-Y)
B = zeros(13,3);
B(11,1) = 1/thrust_Response;
B(12,2) = 1/servo_Response;
B(13,3) = 1/servo_Response;


%Matrix C: Sensor Values 
C = eye(13,13); %Current Matrix Assumes Perfect Sensor Readings


%Matrix D: Feedthrough Matrix (Zeros-Takes time to change values)
D = zeros(13,3);


%Matrix Q: Error Multiplier (How much you care about an error value)
%Q = diag([.5, .5, 50, 1, 1, 1, 1, 1, 1, 1]);
%Q = diag([1/x_max^2, 1/y_max^2, 1/z_max^2, 1/xprime_max^2, ...
%          1/yprime_max^2, 1/zprime_max^2, 1/thetaX_max^2, ...
%         1/thetaY_max^2, 1/thetaprimeX_max^2, 1/thetaprimeY_max^2, ...
%         0.01, 0.01, 0.01]);
% More balanced Q matrix
Q = diag([
    10,     
    10,      
    10,    
    1,      
    1,      
    100,     
    50,     
    50,     
    10,     
    10,     
    0.1,  
    0.01,   
    0.01    
]);

%Matrix R: Control Input Weight (How much fast you want error corrected)
R = diag([1, 10, 10]);
%R = diag([1/thrust_Max^2, 1/gimbalXY_Max^2, 1/gimbalXY_Max^2]);

%Matrix x0: Lander Starting Point
x0 = zeros(13,1);
x0(1) = 0.5;
x0(2) = 0.5;
x0(7) = deg2rad(2);
x0(8) = deg2rad(2);
x0(11) = 0;



%Matrix S: Setpoint Values for System
S = zeros(13,1);
S(3) = 4; %Z height to 4m
S(11) = 0;

%Solve Controllablility and Eigen Values
Co = ctrb(A, B);
fprintf('Controllable rank: %d (need 13)\n', rank(Co))
[K, ~, CL_eigs] = lqr(A, B, Q, R);
fprintf('Closed-loop eigenvalues:\n')
disp(CL_eigs)


%SIMULINK and Graphing Code
simOut = sim('SIMULINK_Module');
x_out = simOut.x_out;
run('Plot_LQR_Results.m');




