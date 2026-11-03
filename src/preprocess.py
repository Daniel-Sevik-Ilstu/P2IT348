"""Step 3: year split, log1p, feature filters and scaling (fit on training years only)."""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from src.config import (
    LABEL_COL,
    MIN_SUPPORT,
    TEST_YEARS,
    TRAIN_YEARS,
    TUNE_TRAIN_YEARS,
    TUNE_VAL_YEAR,
    YEAR_COL,
    Z_CLIP,
)
from src.data import feature_columns


def check_no_overlap(train_years: Iterable[int], test_years: Iterable[int]) -> None:
    """Raise ValueError unless train and test years are non-empty, disjoint, and every train year precedes every test year."""
    train, test = set(train_years), set(test_years)
    if not train or not test:
        raise ValueError("train_years and test_years must both be non-empty")
    if train & test:
        raise ValueError(f"train and test years overlap: {sorted(train & test)}")
    if max(train) >= min(test):
        raise ValueError(f"training years {sorted(train)} must all precede test years {sorted(test)}")


def split_by_year(
    df: pd.DataFrame,
    train_years: Iterable[int] = TRAIN_YEARS,
    test_years: Iterable[int] = TEST_YEARS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (train, test) frames selected by the `year` column, after checking the years cannot leak."""
    train_years, test_years = tuple(train_years), tuple(test_years)
    check_no_overlap(train_years, test_years)  # guard first: nothing is selected for a bad split
    train = df[df[YEAR_COL].isin(train_years)]
    test = df[df[YEAR_COL].isin(test_years)]
    return train, test


def apply_log1p(X: np.ndarray) -> np.ndarray:
    """Return log(1 + X) as float32; raises ValueError on negative input (counts must be >= 0)."""
    if X.size and X.min() < 0:
        raise ValueError("log1p input must be non-negative")
    return np.log1p(X, dtype=np.float32)


def nonzero_feature_mask(X_train: np.ndarray, min_support: int = MIN_SUPPORT) -> np.ndarray:
    """Boolean mask of columns with at least `min_support` non-zero values in the TRAINING rows."""
    return (X_train != 0).sum(axis=0) >= min_support


class Preprocessor:
    """log1p -> minimum-support column filter -> StandardScaler, all learned from training rows only."""

    def __init__(self, min_support: int = MIN_SUPPORT) -> None:
        """Store the support threshold; nothing is learned until `fit`."""
        self.min_support = min_support
        self.scaler: StandardScaler | None = None
        self.mask_: np.ndarray | None = None
        self.feature_names_in_: list[str] | None = None
        self.kept_features_: list[str] | None = None
        self.n_all_zero_: int = 0

    def fit(self, X_train_raw: np.ndarray, feature_names: list[str] | None = None) -> "Preprocessor":
        """Learn the column mask and the scaler from raw training counts."""
        X = apply_log1p(X_train_raw)  # log1p keeps zeros at zero, so the mask is the same on raw or logged data
        self.mask_ = nonzero_feature_mask(X, self.min_support)
        self.n_all_zero_ = int((~(X != 0).any(axis=0)).sum())
        names = feature_names if feature_names is not None else [str(i) for i in range(X.shape[1])]
        self.feature_names_in_ = list(names)
        self.kept_features_ = [n for n, keep in zip(names, self.mask_) if keep]
        self.scaler = StandardScaler().fit(X[:, self.mask_])
        return self

    def transform(self, X_raw: np.ndarray, clip: bool = True) -> np.ndarray:
        """Apply the fitted log1p, mask and scaler (never refits), clip to +-Z_CLIP; returns float32.

        `clip=False` is only for reporting the size of the extreme values.
        """
        if self.scaler is None or self.mask_ is None:
            raise RuntimeError("Preprocessor must be fit before transform")
        X = apply_log1p(X_raw)[:, self.mask_]
        Z = self.scaler.transform(X).astype(np.float32)
        # Fixed constant clip: the same for train and test, nothing learned from any data.
        return np.clip(Z, -Z_CLIP, Z_CLIP, out=Z) if clip else Z

    def fit_transform(self, X_train_raw: np.ndarray, feature_names: list[str] | None = None) -> np.ndarray:
        """Fit on the training counts and return them transformed."""
        return self.fit(X_train_raw, feature_names).transform(X_train_raw)


def _split_arrays(train: pd.DataFrame, test: pd.DataFrame, features: list[str]) -> dict:
    """Pull raw feature matrices, labels and years out of the train/test frames."""
    return {
        "X_train_raw": train[features].to_numpy(dtype=np.float32),
        "y_train": train[LABEL_COL].to_numpy(),
        "years_train": train[YEAR_COL].to_numpy(),
        "X_test_raw": test[features].to_numpy(dtype=np.float32),
        "y_test": test[LABEL_COL].to_numpy(),
        "years_test": test[YEAR_COL].to_numpy(),
    }


def prepare_split(
    df: pd.DataFrame,
    train_years: Iterable[int] = TRAIN_YEARS,
    test_years: Iterable[int] = TEST_YEARS,
) -> dict:
    """Split by year, fit a Preprocessor on the training rows only, transform both sides with it."""
    features = feature_columns(df)
    train, test = split_by_year(df, train_years, test_years)
    a = _split_arrays(train, test, features)
    X_train_raw, X_test_raw = a.pop("X_train_raw"), a.pop("X_test_raw")
    pre = Preprocessor().fit(X_train_raw, features)  # training rows only
    X_train, X_test = pre.transform(X_train_raw, clip=False), pre.transform(X_test_raw, clip=False)
    clip_stats = clip_report(X_train, X_test)  # measured before clipping
    np.clip(X_train, -Z_CLIP, Z_CLIP, out=X_train)
    np.clip(X_test, -Z_CLIP, Z_CLIP, out=X_test)
    return {"X_train": X_train, "X_test": X_test, "preprocessor": pre, "clip_stats": clip_stats, **a}


def clip_report(X_train: np.ndarray, X_test: np.ndarray) -> pd.DataFrame:
    """Max abs z and number of entries beyond +-Z_CLIP for UNCLIPPED scaled matrices; also the values after clipping."""
    rows = []
    for side, X in (("train", X_train), ("test", X_test)):
        A = np.abs(X)
        rows.append((side, float(A.max()), int((A > Z_CLIP).sum()), float(min(A.max(), Z_CLIP)), 0))
    return pd.DataFrame(rows, columns=["side", "max_abs_z_before", "n_clipped", "max_abs_z_after", "n_beyond_clip_after"])


def make_tuning_split(df: pd.DataFrame) -> dict:
    """Same as `prepare_split`, but train on 2014-2015 and validate on 2016 (for tuning only)."""
    return prepare_split(df, TUNE_TRAIN_YEARS, (TUNE_VAL_YEAR,))


def filter_report(df: pd.DataFrame, pre: Preprocessor, train_years: Iterable[int], test_years: Iterable[int]) -> pd.DataFrame:
    """Feature counts after each filter, plus columns active in the test years but dropped by the training-only mask."""
    features = feature_columns(df)
    test = df[df[YEAR_COL].isin(tuple(test_years))]
    test_active = (test[features].to_numpy() != 0).any(axis=0)
    n_total = len(features)
    n_nonzero = n_total - pre.n_all_zero_
    n_kept = int(pre.mask_.sum())
    rows = [
        ("raw features", n_total),
        ("after dropping all-zero training columns", n_nonzero),
        (f"after min support >= {pre.min_support} training rows", n_kept),
        ("dropped for low support (1 to min_support-1 non-zero rows)", n_nonzero - n_kept),
        ("dropped columns that are non-zero somewhere in the test years", int((test_active & ~pre.mask_).sum())),
    ]
    return pd.DataFrame(rows, columns=["stage", "n_features"])


def split_table(split: dict) -> pd.DataFrame:
    """Rows and class balance per year on each side of the split."""
    rows = []
    for side in ("train", "test"):
        years, y = split[f"years_{side}"], split[f"y_{side}"]
        for year in sorted(set(years)):
            m = years == year
            rows.append((side, int(year), int(m.sum()), int(y[m].sum()), int((1 - y[m]).sum())))
    return pd.DataFrame(rows, columns=["side", "year", "rows", "malware", "benign"])
