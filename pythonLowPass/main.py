# Logging
import logging
from pathlib import Path

import numpy as np
from scipy.signal import butter, filtfilt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === Base Signal ===
data_dir = Path("../data")

source_dir = data_dir / "source"
results_dir = data_dir / "results"


def main() -> None:
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)

    # Load data (skip header)
    no_noise_data = np.loadtxt(
        source_dir / "sine_wave_no_noise.txt",
        delimiter=",",
        skiprows=1,
    )
    with_noise_data = np.loadtxt(
        source_dir / "sine_wave_with_noise.txt",
        delimiter=",",
        skiprows=1,
    )

    # Extract columns
    t = no_noise_data[:, 0]
    # signal = no_noise_data[:, 1]
    noisy_signal = with_noise_data[:, 1]

    # Compute sampling rate
    sampling_rate = len(t) / (t[-1] - t[0])
    logger.info("Sampling rate: %s Hz", sampling_rate)

    # === Filtering ===
    cutoff_frequencies = [3, 6, 12, 20]  # Hz

    filtered_signals = []

    for cutoff in cutoff_frequencies:
        normalized_cutoff = cutoff / (sampling_rate / 2)
        # Design filter
        b, a = butter(4, normalized_cutoff, btype="low")

        # Apply filter
        filtered_signal = filtfilt(b, a, noisy_signal)
        filtered_signals.append(filtered_signal)

        # Create filename
        filename = f"python_results_{cutoff}_hz.txt"
        filepath = results_dir / filename

        # Write to file
        with filepath.open("w", encoding="utf-8") as f:
            f.write("time,value\n")
            for ti, yi in zip(t, filtered_signal, strict=False):
                f.write(f"{ti},{yi}\n")

    logger.info("Filtering complete. Files written to: %s", results_dir)


if __name__ == "__main__":
    main()
