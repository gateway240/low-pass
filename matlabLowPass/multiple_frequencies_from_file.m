clear;
%% Base Signal (same every time)
data_dir = "../data"; % Adjust this path as needed

source_dir = fullfile(data_dir,"source");
results_dir = fullfile(data_dir,"results");

% Load the sine wave data (no noise)
no_noise_file = fullfile(source_dir, "sine_wave_no_noise.txt");
no_noise_data = readtable(no_noise_file);

% Load the noisy sine wave data
with_noise_file = fullfile(source_dir, "sine_wave_with_noise.txt");
with_noise_data = readtable(with_noise_file);

t = no_noise_data.time; % Time column (same for both files)
signal = no_noise_data.value; % Sine wave without noise
noisy_signal = with_noise_data.value; % Sine wave with noise

sampling_rate = length(t) / (t(end) - t(1));    % Sampling frequency (Hz)
fprintf("Sampling rate: %f\n",sampling_rate)

%% Different filter cutoffs
cutoff_frequencies = [3, 6, 12, 20]; % Hz

filtered_signals = zeros(length(cutoff_frequencies), length(t));

for i = 1:length(cutoff_frequencies)
    cutoff = cutoff_frequencies(i);
    normalized_cutoff = cutoff / (sampling_rate / 2);
    [b, a] = butter(4, normalized_cutoff, 'low');
    % Apply filter
    filtered_signal = filtfilt(b, a, noisy_signal);
    filtered_signals(i, :) = filtered_signal;
    % Create filename dynamically
    filename = sprintf("matlab_results_%d_hz.txt", cutoff);
    filepath = fullfile(results_dir, filename);

    % Write to file (time, value)
    fileID = fopen(filepath, 'w');
    fprintf(fileID, "time,value\n");

    for j = 1:length(t)
        fprintf(fileID, "%.16f,%.16f\n", t(j), filtered_signal(j));
    end

    fclose(fileID);
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
