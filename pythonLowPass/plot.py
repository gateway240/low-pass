import logging
import operator
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define the directory containing the results
data_dir = Path("../data")
results_dir = data_dir / "results"
source_dir = data_dir / "source"

# Load the original (no noise) and noisy signal
no_noise_data = np.loadtxt(
    source_dir / "sine_wave_no_noise.txt", delimiter=",", skiprows=1
)
with_noise_data = np.loadtxt(
    source_dir / "sine_wave_with_noise.txt", delimiter=",", skiprows=1
)

# Extract time and signal for original and noisy
t = no_noise_data[:, 0]
signal_no_noise = no_noise_data[:, 1]
signal_with_noise = with_noise_data[:, 1]


# Get all files that match the pattern (e.g., anything_*)
result_files = list(results_dir.glob("*_results_*.txt"))

# Define line styles for each modality
line_styles = {
    "matlab": "-",
    "python": "--",
    "other": ":",  # Default style for any other modalities
}
# Initialize a dictionary to hold the data for each frequency
results = {}

# Read all result files
for file in result_files:
    # Extract the frequency from the filename
    filename = Path(file).name
    frequency = int(
        filename.split("_")[2].split(".")[0]
    )  # Extract frequency from filename

    # Load the data (skip header)
    data = np.loadtxt(file, delimiter=",", skiprows=1)

    # Extract time and value columns
    t = data[:, 0]
    signal = data[:, 1]

    # Store the results for each frequency
    if frequency not in results:
        results[frequency] = []

    results[frequency].append((filename, t, signal))
# Sort results by frequency
sorted_results = sorted(results.items(), key=operator.itemgetter(0))
# Plot the results
num_frequencies = len(sorted_results)
fig, axes = plt.subplots(num_frequencies, 1, figsize=(10, 6 * num_frequencies))

if num_frequencies == 1:
    axes = [axes]  # To handle the case where there is only one subplot

for i, (frequency, result_files) in enumerate(sorted_results):
    ax = axes[i]
    ax.set_title(f"Results for {frequency} Hz")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")

    # Plot the original (no noise) and noisy signal
    ax.plot(t, signal_no_noise, label="Original Signal", color="black", linestyle=":")
    ax.plot(t, signal_with_noise, label="Noisy Signal", color="red", linestyle=":")

    # Plot each modality (e.g., MATLAB, Python, others) for the current frequency
    for filename, t, signal in result_files:
        label = filename.split("_")[
            0
        ]  # Label based on the prefix (e.g., "matlab", "python", etc.)
        # Choose line style based on the file prefix
        line_style = line_styles.get(label, "-")  # Default to solid line if not found

        ax.plot(t, signal, label=label, linestyle=line_style)

    ax.legend()
    ax.grid()


# Save the results as a figure
output_file = data_dir / "results_plot.png"  # Define the output file path

plt.tight_layout()
plt.savefig(output_file, format="png")  # Save as PNG file

logger.info("Plot saved to %s", output_file)
