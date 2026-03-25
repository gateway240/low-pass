%% Base Signal (same every time)
rng(42);  % fixed integer seed

frequency = 5; % Signal frequency (Hz)
amplitude = 1;
sampling_rate = 100;
duration = 1;

t = linspace(0, duration, sampling_rate * duration);

% Original signal
signal = amplitude * sin(2 * pi * frequency * t);

% Add noise ONCE
noise_amplitude = 0.3;
noise = noise_amplitude * randn(size(t));
noisy_signal = signal + noise;

%% Different filter cutoffs
cutoff_frequencies = [3, 6, 12, 20]; % Hz

filtered_signals = zeros(length(cutoff_frequencies), length(t));

for i = 1:length(cutoff_frequencies)
    cutoff = cutoff_frequencies(i);
    normalized_cutoff = cutoff / (sampling_rate / 2);

    [b, a] = butter(4, normalized_cutoff, 'low');
    filtered_signals(i, :) = filtfilt(b, a, noisy_signal);
end

%% Plot EVERYTHING on same figure with styles
figure;
hold on;

% Original (bold solid black)
plot(t, signal, 'k-', 'LineWidth', 2.5);

% Noisy (thin dotted red)
plot(t, noisy_signal, 'r:', 'LineWidth', 1.5);

% Style options
line_styles = {'--', '-.', '--', ':'};
% colors = lines(length(cutoff_frequencies));
colors = {'c','m','y','g'};

% Filtered signals with mixed styles
for i = 1:length(cutoff_frequencies)
    plot(t, filtered_signals(i, :), ...
        'LineStyle', line_styles{i}, ...
        'Color', colors{i}, ...
        'LineWidth', 2);
end

xlabel('Time (s)');
ylabel('Amplitude');
title('Effect of Filter Frequency');

legend_entries = [{'Original'}, {'Noisy'}, ...
    arrayfun(@(c) ['Filtered (' num2str(c) ' Hz)'], cutoff_frequencies, 'UniformOutput', false)];
legend(legend_entries, 'Location', 'best');

grid on;
