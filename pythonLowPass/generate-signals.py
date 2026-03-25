# Logging
import logging
import pathlib

import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_dir = pathlib.Path("..") / "data" / "source"


def main() -> None:
    logger.info("Hello from pythonlowpass!")
    # Parameters
    frequency = 2  # Frequency of the sine wave in Hz
    amplitude = 1  # Amplitude of the sine wave
    sampling_rate = 100  # Samples per second
    duration = 1  # Duration in seconds

    # Time vector
    t = np.linspace(0, duration, int(sampling_rate * duration))

    # Generate sine wave without noise
    sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)

    # Fix the seed for reproducibility
    rng = np.random.default_rng(42)

    # Add Gaussian noise (mean, std)
    noise = rng.normal(0, 0.3, sine_wave.shape)
    sine_wave_with_noise = sine_wave + noise

    # Write the signals to a text file
    file_no_noise = base_dir / "sine_wave_no_noise.txt"
    file_with_noise = base_dir / "sine_wave_with_noise.txt"

    # Write the clean sine wave to a file
    with file_no_noise.open("w", encoding="utf-8") as f:
        f.write("time,value\n")  # Column headers
        for i in range(len(t)):
            f.write(f"{t[i]}, {sine_wave[i]}\n")

    # Write the noisy sine wave to a file
    with file_with_noise.open("w", encoding="utf-8") as f:
        f.write("time,value\n")  # Column headers
        for i in range(len(t)):
            f.write(f"{t[i]}, {sine_wave_with_noise[i]}\n")


if __name__ == "__main__":
    main()
