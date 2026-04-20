# Logging
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

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
    fp_right_origins = origins[fp_right - 1]
    logger.info("Origins for FP [%s]:\n %s", fp_right, fp_right_origins)

    # Force place data is extracted. Now process data

    logger.info("Filtering complete. Files written to: %s", results_dir)


if __name__ == "__main__":
    main()
