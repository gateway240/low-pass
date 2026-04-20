%% Logging equivalent (MATLAB uses simple command window output)
% You can replace with fprintf or logging functions if needed

clear; clc;

%% === Base Signal ===
data_dir = fullfile(getenv('HOME'), 'data', 'low-pass-testing');

source_dir = fullfile(data_dir, 'source');
results_dir = fullfile(data_dir, 'results');

if ~exist(results_dir, 'dir')
    mkdir(results_dir);
end

CUTOFF = 6;          % Hz
FILTER_ORDER = 3;
GRF_CUTOFF = 20;     % N

fp_right = 5;
fp_left = 4;

START = 40;
END_ = 45;

%% === Read STO file ===
[file_headers, data] = read_sto_file(fullfile(data_dir, 'walking_grfs.sto'));

disp(file_headers);

%% Extract corner/origin data
raw_corners = file_headers('Corners');
corners = extract_matrix(raw_corners);
%%
fp_right_corners = corners{fp_right};

fp_right_mean_corners = mean(fp_right_corners, 2);

fp_right_ref_frame = compute_pf_reference_frame(fp_right_corners);

raw_origins = file_headers('Origins');
origins = extract_matrix(raw_origins);
fp_right_origin = origins{fp_right};

%% Filter relevant columns
vars = data.Properties.VariableNames;
mask = contains(vars, num2str(fp_right)) | strcmp(vars, 'time');
data_fp = data(:, mask);

filtered_data = butter_lowpass_filter(data_fp, CUTOFF, FILTER_ORDER);

%% Process data
results = process_data(filtered_data, fp_right, ...
    fp_right_ref_frame, fp_right_mean_corners, fp_right_origin);

writetable(results, fullfile(results_dir, 'test-matlab.csv'));

plot_data(results, fp_right, fullfile(results_dir, 'grf-output-matlab.png'), START,END_);

disp("Filtering complete.");

%% ================= FUNCTIONS =================

function [headers, data] = read_sto_file(file_path)
    fid = fopen(file_path, 'r');
    headers = containers.Map();

    tline = fgetl(fid);

    while ischar(tline)
        if contains(tline, '=')
            parts = split(tline, '=');
            headers(strtrim(parts{1})) = strtrim(parts{2});
        end

        if strcmp(strtrim(tline), 'endheader') || isempty(tline)
            break;
        end

        tline = fgetl(fid);
    end
    
    data = readtable(file_path, 'FileType', 'text', ...
        'Delimiter', '\t', ...
        'VariableNamingRule', 'preserve');
    % Rename first column to 'time'
    data.Properties.VariableNames{1} = 'time';
    fclose(fid);
end

function arrays = extract_matrix(s)
    s = extractBetween(s, "{", "}");

    parts = split(s, ',');

    arrays = cell(size(parts));

    for i = 1:length(parts)
        item = parts{i};
        tokens = regexp(item, '\[(.*?)\]', 'tokens');
        group = [];
        for j = 1:length(tokens)
            nums = str2num(tokens{j}{1});%#ok<ST2NM>
            group = [group; nums];
        end

        arrays{i} = group;
    end
end

function v = normalize(v)
    v = v / norm(v);
end

function frame = compute_pf_reference_frame(corners)
    axis_x = corners(:,1) - corners(:,2);
    axis_y = corners(:,1) - corners(:,4);
    axis_z = cross(axis_x, axis_y);
    axis_y = cross(axis_z, axis_x);

    axis_x = normalize(axis_x);
    axis_y = normalize(axis_y);
    axis_z = normalize(axis_z);

    frame = [axis_x(:)'; axis_y(:)'; axis_z(:)'];
end

function filtered_df = butter_lowpass_filter(data, cutoff, order)
    t = data.time;
    fs = height(data) / (t(end) - t(1));

    Wn = cutoff / (fs/2);
    [b,a] = butter(order, Wn, 'low');

    varNames = data.Properties.VariableNames;
    signalIdx = ~strcmp(varNames, 'time');

    X = data{:, signalIdx};
    Xf = filtfilt(b, a, X);

    filtered_df = data;
    filtered_df{:, signalIdx} = Xf;
end

function results = process_data(data, num, ref_frame, mean_corners, origin)

    results = data;

    f = results{:, {sprintf('f%d_1',num), sprintf('f%d_2',num), sprintf('f%d_3',num)}};
    m = results{:, {sprintf('m%d_1',num), sprintf('m%d_2',num), sprintf('m%d_3',num)}};

    m = m + cross(f, repmat(origin', size(f, 1), 1), 2);

    fz = f(:,3);
    valid = -fz >= 20;

    cop_raw = [ ...
        -m(:,2)./fz, ...
         m(:,1)./fz, ...
         zeros(size(fz))];

    force = (ref_frame * f')';
    moment = (ref_frame * m')';
    mean_corners = mean_corners(:)';
    cop = (ref_frame * cop_raw')' + mean_corners;

    cop(~valid,:) = NaN;

    results{:, {sprintf('f%d_1',num), sprintf('f%d_2',num), sprintf('f%d_3',num)}} = force;
    results{:, {sprintf('m%d_1',num), sprintf('m%d_2',num), sprintf('m%d_3',num)}} = moment;
    results{:, {sprintf('p%d_1',num), sprintf('p%d_2',num), sprintf('p%d_3',num)}} = cop;
end

function plot_data(df, num, output_path, t_start, t_end)

    time = df.time;
    time_slice = (time >= t_start) & (time <= t_end);
    df_slice = df(time_slice, :);
    
    figure('Position', [100 100 1200 600]);
    vars = df_slice.Properties.VariableNames;
    n = numel(vars);

    for i = 1:n
        subplot(n, 1, i);
        plot(df_slice.time, df_slice{:, i});
        title(vars{i}, 'Interpreter', 'none');
        ylabel(vars{i}, 'Interpreter', 'none');
        grid on;
    end

    xlabel('Time');
    saveas(gcf, output_path);
end