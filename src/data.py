"""Step 1: load the 16 CSV files, drop apkname, add label and year, combine."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    ALL_YEARS,
    ID_COL,
    LABEL_COL,
    N_RAW_COLUMNS,
    YEAR_COL,
    DATA_DIR,
)

# Year and class come ONLY from the file name.
_FILENAME_RE = re.compile(r"^sampled_(\d{4})_(malware|benign)_api\.csv$")
_CLASS_TO_LABEL = {"malware": 1, "benign": 0}


def parse_filename(name: str) -> tuple[int, int]:
    """Return (year, label) from a file name; label 1 = malware, 0 = benign.

    Raises ValueError for any name that is not exactly
    sampled_<YEAR>_<malware|benign>_api.csv, for a year outside 2014-2021,
    or for a path that contains directories.
    """
    if Path(name).name != name:
        raise ValueError(f"Expected a bare file name, got a path: {name!r}")
    match = _FILENAME_RE.match(name)
    if match is None:
        raise ValueError(f"File name does not match sampled_<YEAR>_<class>_api.csv: {name!r}")
    year = int(match.group(1))
    if year not in ALL_YEARS:
        raise ValueError(f"Year {year} outside {ALL_YEARS[0]}-{ALL_YEARS[-1]}: {name!r}")
    return year, _CLASS_TO_LABEL[match.group(2)]


def list_data_files(data_dir: Path = DATA_DIR) -> list[Path]:
    """List the dataset CSVs, validating every name.

    macOS resource-fork files (name starting with "._") are skipped. Every other
    *.csv must parse, so a stray or misnamed CSV raises ValueError. Also raises
    unless there is exactly one malware and one benign file per year (16 files).
    """
    files = sorted(p for p in Path(data_dir).glob("*.csv") if not p.name.startswith("._"))
    seen: set[tuple[int, int]] = set()
    for path in files:
        key = parse_filename(path.name)  # raises on a stray file
        if key in seen:
            raise ValueError(f"Duplicate year/class file: {path.name}")
        seen.add(key)
    expected = {(y, lab) for y in ALL_YEARS for lab in (0, 1)}
    if seen != expected:
        raise ValueError(f"Missing files (year, label): {sorted(expected - seen)}")
    return files


def read_header(path: Path) -> list[str]:
    """Return the CSV header (all 1,849 raw column names) without reading rows."""
    return list(pd.read_csv(path, nrows=0).columns)


def _check_header(header: list[str], path: Path) -> None:
    """Raise ValueError unless the header has 1,849 unique columns starting with apkname."""
    if len(header) != N_RAW_COLUMNS:
        raise ValueError(f"{path.name}: expected {N_RAW_COLUMNS} columns, found {len(header)}")
    if header[0] != ID_COL:
        raise ValueError(f"{path.name}: first column is {header[0]!r}, expected {ID_COL!r}")
    if len(set(header)) != len(header):
        raise ValueError(f"{path.name}: duplicate column names in header")


def load_file(path: Path) -> pd.DataFrame:
    """Load one CSV: drop the first column (apkname), cast features to int32.

    Adds `label` (int8) and `year` (int16) taken from the file name. The first
    column is dropped by position after confirming it is apkname. Does not
    assume a row count. Raises ValueError for a wrong column count, missing or
    non-integer values, or negative values.
    """
    year, label = parse_filename(Path(path).name)
    header = read_header(path)
    _check_header(header, path)
    features = header[1:]
    # usecols by position skips the identifier column entirely.
    try:
        df = pd.read_csv(path, usecols=range(1, N_RAW_COLUMNS), dtype=np.int32)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"{path.name}: non-integer, missing or out-of-range values ({exc})") from exc
    if list(df.columns) != features:
        raise ValueError(f"{path.name}: columns changed while reading")
    if int(df.to_numpy().min(initial=0)) < 0:
        raise ValueError(f"{path.name}: negative feature values")
    # Add both columns in one concat (inserting one by one fragments the frame).
    extra = pd.DataFrame(
        {
            LABEL_COL: np.full(len(df), label, dtype=np.int8),
            YEAR_COL: np.full(len(df), year, dtype=np.int16),
        },
        index=df.index,
    )
    return pd.concat([df, extra], axis=1)


def read_apknames(path: Path) -> pd.Series:
    """Return only the apkname column (used for the duplicate audit, never as a feature)."""
    return pd.read_csv(path, usecols=[0]).iloc[:, 0]


def load_year(year: int, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Concatenate one year's malware and benign files (in that order of the file list)."""
    parts = [load_file(p) for p in list_data_files(data_dir) if parse_filename(p.name)[0] == year]
    if len(parts) != 2:
        raise ValueError(f"Year {year}: expected 2 files, found {len(parts)}")
    validate_feature_order(parts)
    return pd.concat(parts, ignore_index=True)


def feature_columns(df: pd.DataFrame) -> list[str]:
    """All columns except label and year (the 1,848 API-call features)."""
    return [c for c in df.columns if c not in (LABEL_COL, YEAR_COL)]


def validate_feature_order(frames: list[pd.DataFrame]) -> None:
    """Raise ValueError if any frame's feature columns differ from the first in names or order."""
    reference = feature_columns(frames[0])
    for i, frame in enumerate(frames[1:], start=1):
        if feature_columns(frame) != reference:
            raise ValueError(f"Feature columns of frame {i} differ from frame 0 (names or order)")


def combine_years(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Concatenate per-year frames in year order into one frame with a fresh index."""
    ordered = [frames[y] for y in sorted(frames)]
    validate_feature_order(ordered)
    return pd.concat(ordered, ignore_index=True)
