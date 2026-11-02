"""Step 1: load the 16 CSV files, drop apkname, add label and year, combine."""
from __future__ import annotations

import csv
import hashlib
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    ALL_YEARS,
    CACHE_DIR,
    CACHE_SCHEMA_VERSION,
    TRAIN_YEARS,
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
    # csv module keeps raw names; pandas would rename duplicates (f -> f.1).
    with open(path, newline="", encoding="utf-8-sig") as f:
        return next(csv.reader(f))


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
    if len(df) == 0:
        raise ValueError(f"{path.name}: file has no data rows")
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


def check_schema(df: pd.DataFrame, expected_features: list[str]) -> None:
    """Raise ValueError unless df has the expected features (in order), no negatives, label in {0,1}, year in 2014-2021, no NaN."""
    if feature_columns(df) != expected_features:
        raise ValueError("Feature columns differ from the CSV header (names or order)")
    if len(expected_features) != N_RAW_COLUMNS - 1:
        raise ValueError(f"Expected {N_RAW_COLUMNS - 1} feature columns, found {len(expected_features)}")
    if LABEL_COL not in df.columns or YEAR_COL not in df.columns:
        raise ValueError("label or year column missing")
    if int(df[expected_features].to_numpy().min(initial=0)) < 0:
        raise ValueError("Negative feature values")
    if df[[LABEL_COL, YEAR_COL]].isna().any().any():
        raise ValueError("label or year contains missing values (columns of different length?)")
    if not df[LABEL_COL].isin([0, 1]).all():
        raise ValueError("label must be 0 or 1")
    if not df[YEAR_COL].isin(ALL_YEARS).all():
        raise ValueError(f"year must be in {ALL_YEARS[0]}-{ALL_YEARS[-1]}")


def cache_key(data_dir: Path = DATA_DIR) -> str:
    """Hash of every CSV name, size and mtime plus CACHE_SCHEMA_VERSION."""
    h = hashlib.sha256(f"schema={CACHE_SCHEMA_VERSION}".encode())
    for path in list_data_files(data_dir):
        st = path.stat()
        h.update(f"|{path.name}:{st.st_size}:{st.st_mtime_ns}".encode())
    return h.hexdigest()[:16]


def _cache_path(key: str, cache_dir: Path) -> Path:
    """Cache file location for a key."""
    return Path(cache_dir) / f"step1_data_{key}.npz"


def _write_cache(df: pd.DataFrame, key: str, cache_dir: Path) -> None:
    """Store features (int32), label, year and the feature column names; drop stale caches."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    for old in cache_dir.glob("step1_data_*.npz"):
        old.unlink()
    feats = feature_columns(df)
    np.savez(
        _cache_path(key, cache_dir),
        X=df[feats].to_numpy(dtype=np.int32),
        label=df[LABEL_COL].to_numpy(),
        year=df[YEAR_COL].to_numpy(),
        columns=np.array(feats, dtype=str),
        key=np.array(key),
    )


def _read_cache(key: str, cache_dir: Path) -> pd.DataFrame | None:
    """Return the cached frame, or None if missing, stale or unreadable."""
    path = _cache_path(key, cache_dir)
    if not path.exists():
        return None
    try:
        with np.load(path, allow_pickle=False) as z:
            if str(z["key"]) != key:
                return None
            feats = [str(c) for c in z["columns"]]
            x, label, year = z["X"], z["label"], z["year"]
            if not (len(x) == len(label) == len(year)):
                return None  # X, label and year must line up
            feature_df = pd.DataFrame(x, columns=feats)
            extra = pd.DataFrame({LABEL_COL: label.astype(np.int8), YEAR_COL: year.astype(np.int16)})
    except (OSError, ValueError, KeyError, EOFError, zipfile.BadZipFile):
        return None  # missing, truncated or corrupt cache: rebuild from the CSVs
    return pd.concat([feature_df, extra], axis=1)


def load_all(
    data_dir: Path = DATA_DIR, use_cache: bool = True, cache_dir: Path = CACHE_DIR
) -> pd.DataFrame:
    """Load the whole dataset (rows x 1,848 features + label + year).

    With use_cache the combined frame is stored in cache/ keyed on file names,
    sizes, mtimes and the schema version. On every cache load the schema is
    re-checked against the first CSV header; a key mismatch or failed check
    rebuilds from the CSVs.
    """
    files = list_data_files(data_dir)
    reference = read_header(files[0])
    _check_header(reference, files[0])
    expected = reference[1:]
    key = cache_key(data_dir)
    if use_cache:
        cached = _read_cache(key, cache_dir)
        if cached is not None:
            try:
                check_schema(cached, expected)
                return cached
            except ValueError:
                pass  # corrupt or altered cache: rebuild below
    frames = {y: load_year(y, data_dir) for y in ALL_YEARS}
    df = combine_years(frames)
    check_schema(df, expected)
    if use_cache:
        _write_cache(df, key, cache_dir)
    return df


def _row_hashes(df: pd.DataFrame) -> np.ndarray:
    """64-bit hash of each row feature vector (collision odds negligible at ~1e5 rows)."""
    return pd.util.hash_pandas_object(df[feature_columns(df)], index=False).to_numpy()


def label_conflict_mask(hashes: np.ndarray, labels: np.ndarray) -> np.ndarray:
    """Boolean mask: True where the row's feature vector occurs with both labels in the given rows."""
    n_labels = pd.Series(labels).groupby(hashes).transform("nunique").to_numpy()
    return n_labels > 1


def train_duplicate_mask(df: pd.DataFrame, train_years: tuple[int, ...] = TRAIN_YEARS) -> np.ndarray:
    """Boolean mask over df: True where a non-training row feature vector also occurs in a training-year row.

    Training-year rows themselves are always False (the mask is for test rows).
    """
    hashes = _row_hashes(df)
    in_train = df[YEAR_COL].isin(train_years).to_numpy()
    mask = np.isin(hashes, hashes[in_train])
    return mask & ~in_train


def summarize_data(df: pd.DataFrame, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """One row per year: counts plus the duplicate / overlap / all-zero audit.

    Columns: year, files, rows, feature_columns, malware, benign,
    duplicate_rows (feature vector already seen earlier in the same year),
    all_zero_columns (zero in every row of the year), repeated_apknames (rows
    whose apkname already appeared earlier in the year), rows_in_earlier_years
    (feature vector occurs in an earlier year), test_rows_in_train and
    test_share_in_train (test years only: vector occurs in 2014-2016),
    conflict_vectors and conflict_rows (distinct feature vectors, and the rows
    carrying them, that occur with both labels within the year).
    """
    feats = feature_columns(df)
    hashes = _row_hashes(df)
    years = df[YEAR_COL].to_numpy()
    dup_train = train_duplicate_mask(df)
    files = list_data_files(data_dir)
    rows = []
    for year in ALL_YEARS:
        sel = years == year
        sub = df.loc[sel]
        year_files = [p for p in files if parse_filename(p.name)[0] == year]
        apknames = pd.concat([read_apknames(p) for p in year_files], ignore_index=True)
        earlier = np.isin(hashes[sel], hashes[years < year])
        is_test = year not in TRAIN_YEARS
        n = int(sel.sum())
        conflict = label_conflict_mask(hashes[sel], sub[LABEL_COL].to_numpy())
        rows.append(
            {
                "year": year,
                "files": len(year_files),
                "rows": n,
                "feature_columns": len(feats),
                "malware": int((sub[LABEL_COL] == 1).sum()),
                "benign": int((sub[LABEL_COL] == 0).sum()),
                "duplicate_rows": int(pd.Series(hashes[sel]).duplicated().sum()),
                "all_zero_columns": int((~sub[feats].to_numpy().any(axis=0)).sum()),
                "repeated_apknames": int(apknames.duplicated().sum()),
                "rows_in_earlier_years": int(earlier.sum()),
                "conflict_vectors": int(pd.Series(hashes[sel][conflict]).nunique()),
                "conflict_rows": int(conflict.sum()),
                "test_rows_in_train": int(dup_train[sel].sum()) if is_test else np.nan,
                "test_share_in_train": float(dup_train[sel].sum() / n) if is_test else np.nan,
            }
        )
    return pd.DataFrame(rows)


def file_table(df: pd.DataFrame, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """One row per file: file, year, class, rows, columns after the drop (features only)."""
    out = []
    n_features = len(feature_columns(df))
    for path in list_data_files(data_dir):
        year, label = parse_filename(path.name)
        rows = int(((df[YEAR_COL] == year) & (df[LABEL_COL] == label)).sum())
        out.append(
            {
                "file": path.name,
                "year": year,
                "class": "malware" if label == 1 else "benign",
                "rows": rows,
                "columns_after_drop": n_features,
            }
        )
    return pd.DataFrame(out)


def _to_markdown(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub Markdown table (no tabulate dependency)."""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        # Whole-number floats (ints that were upcast by NaN in their column) print as ints.
        cells = [
            "" if pd.isna(v) else (str(int(v)) if float(v).is_integer() else f"{v:.4f}") if isinstance(v, (int, float, np.number)) else str(v)
            for v in row
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines) + "\n"


def write_data_summary(summary: pd.DataFrame, path: Path) -> None:
    """Write summary to <path>.csv and <path>.md (path is given without extension)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(path.with_suffix(".csv"), index=False)
    path.with_suffix(".md").write_text(_to_markdown(summary), encoding="utf-8")
