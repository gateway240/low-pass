# Logging
import logging
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === Base Signal ===
data_dir = Path("~/data/low-pass-testing").expanduser()

source_dir = data_dir / "source"
results_dir = data_dir / "results"

CUTOFF = 6  # Hz
FILTER_ORDER = 3
GRF_CUTOFF = 20  # N

# 1 based index to match data header
fp_right = 5
fp_left = 4

START = 40
END = 45


# opensim format
def read_sto_file(
    file_path: Path, sep: str = "\t"
) -> tuple[dict[str, str], pd.DataFrame]:
    headers = {}
    count = 0
    with file_path.open(encoding="utf-8") as file:
        for line in file:
            # logger.info("Count %d, Line: %s", count, line)
            name, var = line.partition("=")[::2]
            headers[name.strip()] = var.strip()
            count += 1
            if line.strip() == "endheader" or not line.strip():
                break

        # Read the rest of the file into a DataFrame
        # Use the remaining lines as the data
        data = pd.read_csv(file, index_col=0, sep=sep)

    return headers, data


def find_between(s: str, start: str, end: str) -> str:
    idx1 = s.find(start)
    idx2 = s.find(end, idx1 + len(start))
    if idx1 == -1 or idx2 == -1:
        msg = f"Start {start} or End {end} delimiter not found"
        raise ValueError(msg)
    return s[idx1 + len(start) : idx2]


def extract_matrix(s: str) -> list[np.ndarray]:
    logger.info(s)

    arrays = find_between(s, "{", "}")

    split = arrays.split(",")

    result = []

    for item in split:
        group = []
        # logger.info(item)
        # Regex: https://stackoverflow.com/a/1454936
        res = re.findall(r"\[(.*?)\]", item)
        # logger.info("Captured: %s", res)
        for parts in res:
            subl = [float(num) for num in parts.split(" ")]
            group.append(subl)
        result.append(np.array(group))

    return result


def normalize(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v)


def compute_pf_reference_frame(corners: np.ndarray) -> np.ndarray:
    axis_x = corners[:, 0] - corners[:, 1]
    axis_y = corners[:, 0] - corners[:, 3]
    axis_z = np.cross(axis_x, axis_y)
    axis_y = np.cross(axis_z, axis_x)

    axis_x = normalize(axis_x)
    axis_y = normalize(axis_y)
    axis_z = normalize(axis_z)

    return np.array([axis_x, axis_y, axis_z])


def compute_mean_corners(corners: np.ndarray) -> np.ndarray:
    return corners.mean(1)


def butter_lowpass_filter(
    data: pd.DataFrame, cutoff: float, order: float
) -> pd.DataFrame:
    sampling_rate = len(data) / (data.index[-1] - data.index[0])
    logger.info("Sampling rate: %s Hz", sampling_rate)

    normalized_cutoff = cutoff / (sampling_rate / 2)
    # Get the filter coefficients
    b, a = butter(order, normalized_cutoff, btype="low")

    cols_to_filter = data.columns
    # logger.info(cols_to_filter)
    filtered_values = filtfilt(b, a, data[cols_to_filter], axis=0)

    filtered_df = data.copy()
    filtered_df[cols_to_filter] = filtered_values

    return filtered_df


# Same logic as ezc3d
def process_data(
    data: pd.DataFrame,
    num: int,
    ref_frame: np.ndarray,
    mean_corners: np.ndarray,
    origin: np.ndarray,
) -> pd.DataFrame:
    results = data.copy()
    # for i, row in results.iterrows():
    # if i == 1:
    #     logger.info("Data [%d]: %s", i, row)
    force_raw = results[[f"f{num}_1", f"f{num}_2", f"f{num}_3"]].to_numpy()
    moment_raw_ = results[[f"m{num}_1", f"m{num}_2", f"m{num}_3"]].to_numpy()
    logger.debug("Raw moment: %s", moment_raw_)
    moment_raw = moment_raw_ + np.cross(force_raw, origin.flatten())
    # logger.info("After %s",moment_raw)
    fz = force_raw[:, 2]
    logger.debug("FZ: %s", -fz)

    # Force is backwards because of the ref frame
    valid = -fz >= GRF_CUTOFF

    cop_raw = np.column_stack([
        np.where(valid, -moment_raw[:, 1] / fz, 0),
        np.where(valid, moment_raw[:, 0] / fz, 0),
        np.zeros_like(fz),
    ])
    # cop_raw[~valid, 0:2] = np.nan
    logger.debug("Ref frame: %s", ref_frame)
    logger.debug("Mean corners: %s", mean_corners)
    # @ is matrix multiply in Python
    force = ref_frame @ force_raw.T
    moment = ref_frame @ moment_raw.T
    # cop = ref_frame @ cop_raw.T + mean_corners.reshape(-1, 1)
    cop = ref_frame @ cop_raw.T + mean_corners.reshape(-1, 1)
    # cop = ref_frame @ (moment_raw - np.cross(force_raw, (-1 * cop_raw))).T
    cop = cop.T
    # This makes it so the invalid values to not plot
    cop[~valid] = np.nan
    logger.debug("Force %s: ", force)
    logger.debug("Moment %s: ", moment)
    logger.debug("COP %s: ", cop)

    results[[f"f{num}_1", f"f{num}_2", f"f{num}_3"]] = force.T
    results[[f"m{num}_1", f"m{num}_2", f"m{num}_3"]] = moment.T
    results[[f"p{num}_1", f"p{num}_2", f"p{num}_3"]] = cop
    return results


def plot_data(df: pd.DataFrame, num: int, output_path: Path) -> None:
    logger.info(df.loc[START:END, f"f{num}_1"])
    logger.info(df.head())

    axes = df.loc[START:END].plot(
        # axes = df.plot(
        subplots=True,
        figsize=(12, 3 * len(df.columns)),
        legend=False,
        sharex=True,
    )

    # Ensure axes is iterable if only one column
    if len(df.columns) == 1:
        axes = [axes]

    for ax, col in zip(axes, df.columns, strict=False):
        ax.set_title(col)  # Set subplot title correctly
        ax.set_ylabel(col)  # Y-axis label
        ax.grid(True)  # noqa: FBT003

    axes[-1].set_xlabel("Time")

    plt.tight_layout()

    # Save instead of show
    plt.savefig(output_path, dpi=100)
    plt.close()


def main() -> None:
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    headers, data = read_sto_file(data_dir / "walking_grfs.sto")
    logger.info(headers)
    logger.info(data)

    raw_corners = headers.get("Corners")
    if not raw_corners:
        msg = "raw corner data not found in header"
        raise ValueError(msg)
    corners = extract_matrix(raw_corners)
    fp_right_corners = corners[fp_right - 1]
    logger.info("Corners for FP [%s]:\n %s", fp_right, fp_right_corners)
    fp_right_mean_corners = compute_mean_corners(fp_right_corners)
    logger.info("Mean Corners for FP [%s]:\n %s", fp_right, fp_right_mean_corners)

    fp_right_ref_frame = compute_pf_reference_frame(fp_right_corners)
    logger.info("Reference Frame for FP [%s]:\n %s", fp_right, fp_right_ref_frame)

    raw_origins = headers.get("Origins")
    if not raw_origins:
        msg = "raw origin data not found in header"
        raise ValueError(msg)
    origins = extract_matrix(raw_origins)
    fp_right_origin = origins[fp_right - 1]
    logger.info("Origins for FP [%s]:\n %s", fp_right, fp_right_origin)

    # Force place data is extracted. Now process data
    data = data.loc[:, data.columns.str.contains(str(fp_right))]
    filtered_data = butter_lowpass_filter(data, cutoff=CUTOFF, order=FILTER_ORDER)
    results = process_data(
        filtered_data,
        fp_right,
        fp_right_ref_frame,
        fp_right_mean_corners,
        fp_right_origin,
    )
    # logger.info(data.head())
    logger.info(filtered_data.head())
    logger.info(results)
    results.to_csv(results_dir / "test-2.csv", na_rep="NaN")
    plot_data(results, fp_right, results_dir / "grf-output.png")
    logger.info("Filtering complete. Files written to: %s", results_dir)


if __name__ == "__main__":
    main()
