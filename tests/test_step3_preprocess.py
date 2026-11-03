"""Step 3 tests: year split, log1p, minimum-support mask, scaler fit on training years only.

Written from ASSIGNMENT.md, AGENTS.md and PLAN.md (Step 3), not from the code.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.config import MIN_SUPPORT, TEST_YEARS, TRAIN_YEARS
from src.preprocess import (
    Preprocessor,
    apply_log1p,
    check_no_overlap,
    make_tuning_split,
    nonzero_feature_mask,
    prepare_split,
    split_by_year,
)

ALL_YEARS = list(range(2014, 2022))
N_PER_YEAR = 40
FEATS = ["f_norm", "f_zero", "f_low9", "f_ok10", "f_testonly", "f_big"]


def make_df(test_shift: float = 0.0, seed: int = 42) -> pd.DataFrame:
    """Synthetic 8-year frame (40 rows per year) with edge-case feature columns."""
    rng = np.random.default_rng(seed)
    frames = []
    for y in ALL_YEARS:
        n = N_PER_YEAR
        is_test = y >= 2017
        d = pd.DataFrame(index=range(n))
        d["f_norm"] = rng.integers(1, 20, n) + (test_shift if is_test else 0)
        d["f_zero"] = 0
        d["f_low9"] = 0
        d["f_ok10"] = 0
        d["f_testonly"] = rng.integers(1, 5, n) if is_test else 0
        d["f_big"] = rng.integers(0, 90000, n)
        d["label"] = np.tile([0, 1], n // 2)
        d["year"] = y
        frames.append(d)
    df = pd.concat(frames, ignore_index=True)
    train_idx = np.flatnonzero(df["year"] <= 2016)
    df.loc[train_idx[:9], "f_low9"] = 3        # 9 non-zero training rows
    df.loc[train_idx[:10], "f_ok10"] = 3       # 10 non-zero training rows
    df.loc[df["year"] >= 2017, "f_low9"] = 5   # plenty of support, but only in test years
    return df.astype({c: "int32" for c in FEATS})


def raw(df: pd.DataFrame) -> np.ndarray:
    """Feature matrix as float32."""
    return df[FEATS].to_numpy(dtype=np.float32)


# ---------- year split / leakage ----------

def test_train_and_test_share_no_years_in_prepare_split():
    s = prepare_split(make_df())
    assert not set(np.unique(s["years_train"])) & set(np.unique(s["years_test"]))


def test_prepare_split_train_years_exactly_2014_2016_and_test_2017_2021():
    s = prepare_split(make_df())
    assert set(np.unique(s["years_train"])) == set(TRAIN_YEARS) == {2014, 2015, 2016}
    assert set(np.unique(s["years_test"])) == set(TEST_YEARS) == {2017, 2018, 2019, 2020, 2021}


def test_every_test_year_is_later_than_every_training_year():
    s = prepare_split(make_df())
    assert s["years_train"].max() < s["years_test"].min()


def test_split_row_counts_and_alignment():
    s = prepare_split(make_df())
    assert len(s["X_train"]) == len(s["y_train"]) == len(s["years_train"]) == 3 * N_PER_YEAR
    assert len(s["X_test"]) == len(s["y_test"]) == len(s["years_test"]) == 5 * N_PER_YEAR


def test_split_by_year_returns_disjoint_rows_of_requested_years():
    tr, te = split_by_year(make_df(), TRAIN_YEARS, TEST_YEARS)
    assert set(tr["year"]) == set(TRAIN_YEARS)
    assert set(te["year"]) == set(TEST_YEARS)
    assert len(tr) + len(te) == 8 * N_PER_YEAR


def test_check_no_overlap_accepts_valid_split():
    check_no_overlap(TRAIN_YEARS, TEST_YEARS)  # must not raise


@pytest.mark.parametrize(
    "train,test",
    [
        ((2014, 2015, 2016), (2016, 2017)),  # shared year
        ((2018, 2019, 2020), (2014,)),       # train after test
        ((2014, 2018), (2016, 2020)),        # interleaved: max(train) >= min(test)
        ((), (2017,)),                       # empty train
        ((2014,), ()),                       # empty test
    ],
)
def test_check_no_overlap_raises_on_bad_splits(train, test):
    with pytest.raises(ValueError):
        check_no_overlap(train, test)


def test_split_by_year_raises_on_overlap():
    with pytest.raises(ValueError):
        split_by_year(make_df(), (2014, 2015, 2016), (2016, 2017))


def test_split_by_year_missing_requested_year_fails_loudly():
    with pytest.raises(ValueError):
        split_by_year(make_df(), (2014, 2015, 2016), (2017, 2030))


def test_prepare_split_missing_test_year_fails_loudly():
    df = make_df()
    df = df[df["year"] != 2019]
    with pytest.raises(ValueError):
        prepare_split(df)  # defaults request 2019 as a test year


def test_tuning_split_uses_2014_2015_train_and_2016_validation_only():
    s = make_tuning_split(make_df())
    assert set(np.unique(s["years_train"])) == {2014, 2015}
    assert set(np.unique(s["years_test"])) == {2016}


# ---------- columns ----------

def test_train_and_test_have_identical_column_count_and_order():
    s = prepare_split(make_df())
    assert s["X_train"].shape[1] == s["X_test"].shape[1]
    pre = s["preprocessor"]
    assert len(pre.kept_features_) == s["X_train"].shape[1]
    order = [FEATS.index(f) for f in pre.kept_features_]
    assert order == sorted(order)  # original column order preserved


def test_transform_gives_same_columns_for_train_and_test_values():
    df = make_df()
    pre = Preprocessor().fit(raw(df[df.year <= 2016]), FEATS)
    a = pre.transform(raw(df[df.year <= 2016]))
    b = pre.transform(raw(df[df.year >= 2017]))
    assert a.shape[1] == b.shape[1]


# ---------- scaler fit on training only ----------

def test_training_columns_have_mean_zero_and_std_one():
    s = prepare_split(make_df())
    assert np.allclose(s["X_train"].mean(axis=0), 0.0, atol=1e-4)
    assert np.allclose(s["X_train"].std(axis=0), 1.0, atol=1e-3)


def test_test_data_is_transformed_not_refit():
    """With a big shift in the test years, test columns must not be centred on their own mean."""
    s = prepare_split(make_df(test_shift=1000.0))
    j = s["preprocessor"].kept_features_.index("f_norm")
    assert s["X_test"][:, j].mean() > 2.0


def test_fitted_statistics_equal_training_only_statistics():
    df = make_df()
    pre = Preprocessor().fit(raw(df[df.year <= 2016]), FEATS)
    logged = np.log1p(raw(df[df.year <= 2016]).astype(np.float64))
    keep = [FEATS.index(f) for f in pre.kept_features_]
    np.testing.assert_allclose(pre.scaler.mean_, logged[:, keep].mean(axis=0), rtol=1e-4, atol=1e-4)
    np.testing.assert_allclose(pre.scaler.scale_, logged[:, keep].std(axis=0), rtol=1e-4, atol=1e-4)


def test_changing_test_rows_does_not_change_fitted_scaler_or_mask():
    p1 = prepare_split(make_df(test_shift=0.0))["preprocessor"]
    p2 = prepare_split(make_df(test_shift=500.0))["preprocessor"]
    np.testing.assert_array_equal(p1.scaler.mean_, p2.scaler.mean_)
    np.testing.assert_array_equal(p1.scaler.scale_, p2.scaler.scale_)
    assert p1.kept_features_ == p2.kept_features_


def test_transform_does_not_modify_fitted_scaler():
    df = make_df()
    pre = Preprocessor().fit(raw(df[df.year <= 2016]), FEATS)
    mean_before, scale_before = pre.scaler.mean_.copy(), pre.scaler.scale_.copy()
    pre.transform(raw(df[df.year >= 2017]))
    np.testing.assert_array_equal(pre.scaler.mean_, mean_before)
    np.testing.assert_array_equal(pre.scaler.scale_, scale_before)


def test_output_is_float32_and_finite():
    s = prepare_split(make_df())
    assert s["X_train"].dtype == np.float32 and s["X_test"].dtype == np.float32
    assert np.isfinite(s["X_train"]).all() and np.isfinite(s["X_test"]).all()


def test_fit_transform_equals_fit_then_transform():
    X = raw(make_df().query("year <= 2016"))
    a = Preprocessor().fit_transform(X, FEATS)
    b = Preprocessor().fit(X, FEATS).transform(X)
    np.testing.assert_allclose(a, b, atol=1e-6)


def test_transform_before_fit_raises():
    with pytest.raises(Exception):
        Preprocessor().transform(np.ones((3, 4), dtype=np.float32))


# ---------- log1p ----------

def test_apply_log1p_equals_numpy_log1p_and_float32():
    X = np.array([[0, 1, 10], [100, 92000, 3]], dtype=np.int32)
    out = apply_log1p(X)
    np.testing.assert_allclose(out, np.log1p(X.astype(np.float64)), rtol=1e-5)
    assert out.dtype == np.float32


def test_apply_log1p_negative_input_raises():
    with pytest.raises(ValueError):
        apply_log1p(np.array([[1.0, -1.0]]))


def test_log1p_compresses_heavy_tail():
    assert apply_log1p(np.array([[92000.0]]))[0, 0] < 12


# ---------- minimum-support mask: training rows only ----------

def test_min_support_constant_is_10():
    assert MIN_SUPPORT == 10


def test_mask_nine_nonzero_dropped_ten_kept():
    X = np.zeros((50, 2), dtype=np.float32)
    X[:9, 0] = 1
    X[:10, 1] = 1
    assert nonzero_feature_mask(X).tolist() == [False, True]


def test_mask_all_zero_column_dropped():
    X = np.zeros((50, 2), dtype=np.float32)
    X[:, 1] = 2
    assert nonzero_feature_mask(X).tolist() == [False, True]


def test_mask_custom_min_support():
    X = np.zeros((50, 1), dtype=np.float32)
    X[:3, 0] = 1
    assert nonzero_feature_mask(X, min_support=3).tolist() == [True]
    assert nonzero_feature_mask(X, min_support=4).tolist() == [False]


def test_preprocessor_drops_zero_low_support_and_test_only_columns():
    kept = set(prepare_split(make_df())["preprocessor"].kept_features_)
    assert "f_zero" not in kept       # all zero
    assert "f_low9" not in kept       # 9 training rows, even though test years have support
    assert "f_testonly" not in kept   # non-zero only in test years: decision uses train only
    assert {"f_norm", "f_ok10", "f_big"} <= kept


def test_mask_ignores_test_rows():
    """Adding lots of test-year support to an all-zero training column must not keep it."""
    df = make_df()
    df.loc[df.year >= 2017, "f_zero"] = 7
    assert "f_zero" not in set(prepare_split(df)["preprocessor"].kept_features_)


def test_dropped_column_cannot_produce_large_zscore_on_test():
    s = prepare_split(make_df())
    assert np.abs(s["X_test"]).max() < 50


def test_constant_nonzero_column_does_not_create_nan_or_inf():
    X = np.ones((30, 2), dtype=np.float32)
    X[:, 1] = np.arange(30)
    out = Preprocessor().fit_transform(X, ["c", "v"])
    assert np.isfinite(out).all()


def test_nan_in_input_raises_or_yields_finite_output():
    X = np.ones((30, 2), dtype=np.float32)
    X[:, 1] = np.arange(30)
    X[3, 1] = np.nan
    try:
        out = Preprocessor().fit_transform(X, ["c", "v"])
    except ValueError:
        return
    assert np.isfinite(out).all(), "NaN silently propagated into the model input"


# ---------- real data (skipped when input_data/ is empty) ----------

def test_real_data_split_has_no_year_overlap_and_matching_columns(real_data_dir):
    from src.data import load_all

    df = load_all(real_data_dir)
    s = prepare_split(df)
    assert set(np.unique(s["years_train"])) == {2014, 2015, 2016}
    assert set(np.unique(s["years_test"])) == {2017, 2018, 2019, 2020, 2021}
    assert s["X_train"].shape[1] == s["X_test"].shape[1] <= 1848
    # Scaled values are clipped to +-10 (PLAN.md), which shifts rare columns' training
    # means by up to ~0.02. Tolerance 0.05 allows that shift with margin, while still
    # catching a scaler that was not fit on the training rows.
    assert np.abs(s["X_train"].mean(axis=0)).max() < 0.05
    assert np.abs(s["X_train"]).max() <= 10.0
    assert np.abs(s["X_test"]).max() <= 10.0
    assert s["X_train"].dtype == np.float32
