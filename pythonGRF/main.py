# Logging
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# === Base Signal ===
data_dir = Path("~/data/low-pass-testing").expanduser()

source_dir = data_dir / "source"
results_dir = data_dir / "results"

filter_order = 3

# 1 based index to match data header
fp_right = 5
fp_left = 4


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


def filter_data(data: pd.DataFrame) -> pd.DataFrame:
    return butter_lowpass_filter(data, cutoff=6, order=4)


# Single row processing for reference
# def process_data(
#     data: pd.DataFrame,
#     num: int,
#     ref_frame: np.ndarray,
#     mean_corners: np.ndarray,
#     origin: np.ndarray,
# ) -> pd.DataFrame:
#     results = data.copy()
#     for i, row in results.iterrows():
#         # if i == 1:
#         #     logger.info("Data [%d]: %s", i, row)
#         force_raw = np.array([row[f"f{num}_1"], row[f"f{num}_2"], row[f"f{num}_3"]])
#         moment_raw = np.array([row[f"m{num}_1"], row[f"m{num}_2"], row[f"m{num}_3"]])
#         # logger.info("Raw moment: %s", moment_raw)
#         moment_raw += np.cross(force_raw, origin.flatten())
#         # logger.info(force_raw[2])
#         # logger.info("After %s",moment_raw)
#         cop_raw = np.array([(-moment_raw[1] / force_raw[2]), (moment_raw[0] / force_raw[2]), 0 ])  # noqa: E501
#         # logger.info(cop_raw)
#         # logger.info("Ref frame: %s", ref_frame)
#         # logger.info("Mean corners: %s", mean_corners)
#         # @ is matrix multiply in Python
#         force = ref_frame @ force_raw.reshape(-1, 1)
#         moment = ref_frame @ moment_raw.reshape(-1, 1)
#         cop = ref_frame @ cop_raw.reshape(-1, 1) + mean_corners.reshape(-1, 1)
#         # logger.info("Force %s: ", force)
#         # logger.info("Moment %s: ", moment)
#         # logger.info("COP %s: ", cop)

#         results.loc[i, f"f{num}_1"] = force[0]
#         results.loc[i, f"f{num}_2"] = force[1]
#         results.loc[i, f"f{num}_3"] = force[2]

#         results.loc[i, f"m{num}_1"] = moment[0]
#         results.loc[i, f"m{num}_2"] = moment[1]
#         results.loc[i, f"m{num}_3"] = moment[2]

#         results.loc[i, f"p{num}_1"] = cop[0]
#         results.loc[i, f"p{num}_2"] = cop[1]
#         results.loc[i, f"p{num}_3"] = cop[2]


#     return results
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
    # logger.info("Raw moment: %s", moment_raw)
    moment_raw = moment_raw_ + np.cross(force_raw, origin.flatten())
    # logger.info(force_raw[2])
    # logger.info("After %s",moment_raw)
    fz = force_raw[:, 2]
    cop_raw = np.column_stack([
        (-moment_raw[:, 1] / fz),
        (moment_raw[:, 0] / fz),
        np.zeros_like(fz),
    ])
    # logger.info(cop_raw)
    # logger.info("Ref frame: %s", ref_frame)
    # logger.info("Mean corners: %s", mean_corners)
    # @ is matrix multiply in Python
    force = ref_frame @ force_raw.T
    moment = ref_frame @ moment_raw.T
    cop = ref_frame @ cop_raw.T + mean_corners.reshape(-1, 1)
    # logger.info("Force %s: ", force)
    # logger.info("Moment %s: ", moment)
    # logger.info("COP %s: ", cop)

    results[[f"f{num}_1", f"f{num}_2", f"f{num}_3"]] = force.T
    results[[f"m{num}_1", f"m{num}_2", f"m{num}_3"]] = moment.T
    results[[f"p{num}_1", f"p{num}_2", f"p{num}_3"]] = cop.T
    return results


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
    filtered_data = filter_data(data)
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
    results.to_csv(results_dir / "test-2.csv")
    logger.info("Filtering complete. Files written to: %s", results_dir)


if __name__ == "__main__":
    main()
