% Reference:
% https://www.mathworks.com/matlabcentral/answers/456746-adding-noise-to-a-sine-wave-signal-and-filtering-that-noise
%% NO Noise
% Generate a sine wave signal without noise
frequency = 2; % Frequency of the sine wave (in Hz)
amplitude = 1; % Amplitude of the sine wave
sampling_rate = 100; % Number of samples per second
duration = 1; % Duration of the signal (in seconds)
t = linspace(0, duration, sampling_rate * duration);
signal = amplitude * sin(2 * pi * frequency * t);
% Plot the sine wave without noise
figure;
plot(t, signal);
xlabel('Time (s)');
ylabel('Amplitude');
title('Sine Wave without Noise');
grid on;

%% With Noise
% Generate random noise
noise_amplitude = 0.2; % Amplitude of the noise
noise = noise_amplitude * randn(size(t));
% Add noise to the signal
noisy_signal = signal + noise;
% Plot the sine wave with noise
figure;
plot(t, noisy_signal);
xlabel('Time (s)');
ylabel('Amplitude');
title('Sine Wave with Noise');
grid on;

%% Filter out Noise
% Apply low-pass filter to remove noise
cutoff_frequency = 6; % Cut-off frequency of the low-pass filter
normalized_cutoff = cutoff_frequency / (sampling_rate / 2);
[b, a] = butter(4, normalized_cutoff, 'low');
filtered_signal = filtfilt(b, a, noisy_signal);

% Plot the filtered signal
figure;
plot(t, filtered_signal);
xlabel('Time (s)');
ylabel('Amplitude');
title('Filtered Sine Wave');
grid on;

%% Plot ALL on same figure
figure;
hold on;
plot(t, signal, 'b', 'LineWidth', 1.5);
plot(t, noisy_signal, 'r');
plot(t, filtered_signal, 'g', 'LineWidth', 1.5);

xlabel('Time (s)');
ylabel('Amplitude');
title('Sine Wave: Original vs Noisy vs Filtered');
legend('Original Signal', 'Noisy Signal', 'Filtered Signal');
grid on;
