%% Plot Results
t = x_out.time;
x = x_out.signals.values;

figure('Name', 'CPCL Lander LQR Response', 'NumberTitle', 'off')

%% Plot 1 — Lateral Position
subplot(3, 2, 1)
plot(t, x(:,1), 'b', 'LineWidth', 2, 'DisplayName', 'X Position')
hold on
plot(t, x(:,2), 'r', 'LineWidth', 2, 'DisplayName', 'Y Position')
yline(S(1), 'b--', 'LineWidth', 1, 'HandleVisibility', 'off')
yline(S(2), 'r--', 'LineWidth', 1, 'HandleVisibility', 'off')
xlabel('Time (s)')
ylabel('Position (m)')
title('Lateral Position')
legend('Location', 'northeast')
grid on
hold off

%% Plot 2 — Altitude
subplot(3, 2, 2)
plot(t, x(:,3), 'g', 'LineWidth', 2, 'DisplayName', 'Altitude')
yline(S(3), 'k--', 'LineWidth', 1, 'DisplayName', 'Target')
xlabel('Time (s)')
ylabel('Altitude (m)')
title('Altitude Z')
legend('Location', 'southeast')
grid on

%% Plot 3 — Lateral Velocity
subplot(3, 2, 3)
plot(t, x(:,4), 'b', 'LineWidth', 2, 'DisplayName', 'X Velocity')
hold on
plot(t, x(:,5), 'r', 'LineWidth', 2, 'DisplayName', 'Y Velocity')
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility', 'off')
xlabel('Time (s)')
ylabel('Velocity (m/s)')
title('Lateral Velocity')
legend('Location', 'northeast')
grid on
hold off

%% Plot 4 — Vertical Velocity
subplot(3, 2, 4)
plot(t, x(:,6), 'g', 'LineWidth', 2, 'DisplayName', 'Z Velocity')
yline(0, 'k--', 'LineWidth', 1, 'DisplayName', 'Target')
xlabel('Time (s)')
ylabel('Velocity (m/s)')
title('Vertical Velocity')
legend('Location', 'northeast')
grid on

%% Plot 5 — Attitude Angles
subplot(3, 2, 5)
plot(t, rad2deg(x(:,7)), 'b', 'LineWidth', 2, 'DisplayName', '\theta_x')
hold on
plot(t, rad2deg(x(:,8)), 'r', 'LineWidth', 2, 'DisplayName', '\theta_y')
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility', 'off')
xlabel('Time (s)')
ylabel('Angle (deg)')
title('Attitude Angles')
legend('Location', 'northeast')
grid on
hold off

%% Plot 6 — Angular Rates
subplot(3, 2, 6)
plot(t, rad2deg(x(:,9)),  'b', 'LineWidth', 2, 'DisplayName', '\theta\dot_x')
hold on
plot(t, rad2deg(x(:,10)), 'r', 'LineWidth', 2, 'DisplayName', '\theta\dot_y')
yline(0, 'k--', 'LineWidth', 1, 'HandleVisibility', 'off')
xlabel('Time (s)')
ylabel('Rate (deg/s)')
title('Angular Rates')
legend('Location', 'northeast')
grid on
hold off