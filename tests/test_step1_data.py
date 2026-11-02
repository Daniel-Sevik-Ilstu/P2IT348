"""Step 1 tests: data loading, label extraction, schema checks, combining.

Synthetic CSVs use the real schema (apkname + 1,848 features) but only a few rows,
so they run in seconds. Real-data tests use the `real_data_dir` fixture.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import data
from config import ALL_YEARS, N_RAW_COLUMNS, TRAIN_YEARS

N_FEAT = N_RAW_COLUMNS - 1
FEATS = [f"Lcom/x/C;->m{i}()V" for i in range(N_FEAT)]


def make_csv(path: Path, n_rows: int = 20, seed: int = 0, feats: list[str] = FEATS,
             first_col: str = "apkname") -> Path:
    """Write a synthetic API-call CSV with an id column and the given feature names."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame(rng.integers(0, 5, size=(n_rows, len(feats))), columns=feats)
    df.insert(0, first_col, [f"app{seed}_{i}.apk" for i in range(n_rows)])
    df.to_csv(path, index=False)
    return path


def make_dir(d: Path, years=ALL_YEARS, n_rows: int = 6) -> Path:
    """Write a complete synthetic dataset (one malware + one benign file per year)."""
    for y in years:
        for k, cls in enumerate(("malware", "benign")):
            make_csv(d / f"sampled_{y}_{cls}_api.csv", n_rows=n_rows, seed=y * 2 + k)
    return d


# ---------- parse_filename ----------

@pytest.mark.parametrize("name,expected", [
    ("sampled_2014_malware_api.csv", (2014, 1)),
    ("sampled_2021_benign_api.csv", (2021, 0)),
    ("sampled_2017_malware_api.csv", (2017, 1)),
])
def test_parse_filename_valid(name, expected):
    assert data.parse_filename(name) == expected


@pytest.mark.parametrize("name", [
    "sampled_2013_malware_api.csv",       # year before range
    "sampled_2022_benign_api.csv",        # year after range
    "sampled_2015_goodware_api.csv",      # bad class
    "sampled_2015_malware_api.csv.bak",   # extra suffix
    "sampled_2015_malware.csv",           # missing _api
    "notes.csv",
    "",
])
def test_parse_filename_invalid_raises(name):
    with pytest.raises(ValueError):
        data.parse_filename(name)


def test_parse_filename_rejects_directory_path():
    with pytest.raises(ValueError):
        data.parse_filename("some/dir/sampled_2015_malware_api.csv")


# ---------- load_file ----------

def test_load_file_drops_first_column(tmp_path):
    df = data.load_file(make_csv(tmp_path / "sampled_2015_malware_api.csv"))
    assert "apkname" not in df.columns
    assert df.columns[0] != "apkname"


def test_load_file_has_1848_features_plus_label_year(tmp_path):
    df = data.load_file(make_csv(tmp_path / "sampled_2015_malware_api.csv"))
    assert len(data.feature_columns(df)) == 1848
    assert "label" in df.columns and "year" in df.columns
    assert df.shape[1] == 1848 + 2
    assert list(data.feature_columns(df)) == FEATS


@pytest.mark.parametrize("name,label,year", [
    ("sampled_2015_malware_api.csv", 1, 2015),
    ("sampled_2019_benign_api.csv", 0, 2019),
])
def test_load_file_label_and_year_from_filename(tmp_path, name, label, year):
    df = data.load_file(make_csv(tmp_path / name))
    assert set(df["label"].unique()) == {label}
    assert set(df["year"].unique()) == {year}


def test_load_file_dtypes(tmp_path):
    df = data.load_file(make_csv(tmp_path / "sampled_2015_malware_api.csv"))
    assert all(df[c].dtype == np.int32 for c in FEATS[:10])
    assert df["label"].dtype == np.int8
    assert df["year"].dtype == np.int16


def test_load_file_does_not_assume_row_count(tmp_path):
    for n in (1, 7, 33):
        p = make_csv(tmp_path / f"sampled_2015_malware_api.csv", n_rows=n)
        assert len(data.load_file(p)) == n


def test_load_file_wrong_column_count_raises(tmp_path):
    p = make_csv(tmp_path / "sampled_2015_malware_api.csv", feats=FEATS[:5])
    with pytest.raises(ValueError):
        data.load_file(p)


def test_load_file_extra_column_raises(tmp_path):
    p = make_csv(tmp_path / "sampled_2015_malware_api.csv", feats=FEATS + ["extra"])
    with pytest.raises(ValueError):
        data.load_file(p)


def test_load_file_wrong_first_column_raises(tmp_path):
    p = make_csv(tmp_path / "sampled_2015_malware_api.csv", first_col="id")
    with pytest.raises(ValueError):
        data.load_file(p)


def test_load_file_bad_filename_raises(tmp_path):
    p = make_csv(tmp_path / "notes.csv")
    with pytest.raises(ValueError):
        data.load_file(p)


def test_load_file_negative_value_raises(tmp_path):
    p = make_csv(tmp_path / "sampled_2015_malware_api.csv")
    df = pd.read_csv(p)
    df.iloc[0, 1] = -1
    df.to_csv(p, index=False)
    with pytest.raises(ValueError):
        data.load_file(p)


def test_load_file_missing_value_raises(tmp_path):
    p = make_csv(tmp_path / "sampled_2015_malware_api.csv")
    df = pd.read_csv(p)
    df.iloc[2, 5] = np.nan
    df.to_csv(p, index=False)
    with pytest.raises(ValueError):
        data.load_file(p)


def test_load_file_no_missing_values_on_valid_input(tmp_path):
    df = data.load_file(make_csv(tmp_path / "sampled_2015_malware_api.csv"))
    assert not df.isna().any().any()


def test_load_file_all_zero_feature_kept(tmp_path):
    """Edge case: an all-zero feature is legal data and must not be dropped or fail."""
    p = make_csv(tmp_path / "sampled_2015_malware_api.csv")
    df = pd.read_csv(p)
    df[FEATS[3]] = 0
    df.to_csv(p, index=False)
    out = data.load_file(p)
    assert FEATS[3] in out.columns and (out[FEATS[3]] == 0).all()


def test_read_apknames_returns_ids_only(tmp_path):
    s = data.read_apknames(make_csv(tmp_path / "sampled_2015_malware_api.csv", n_rows=4))
    assert len(s) == 4
    assert s.iloc[0].startswith("app")


# ---------- list_data_files / load_year ----------

def test_list_data_files_returns_16_sorted(tmp_path):
    make_dir(tmp_path, n_rows=2)
    files = data.list_data_files(tmp_path)
    assert len(files) == 16
    assert files == sorted(files)


def test_list_data_files_stray_csv_raises(tmp_path):
    make_dir(tmp_path, n_rows=2)
    (tmp_path / "notes.csv").write_text("a,b\n1,2\n")
    with pytest.raises(ValueError):
        data.list_data_files(tmp_path)


def test_list_data_files_missing_file_raises(tmp_path):
    make_dir(tmp_path, n_rows=2)
    (tmp_path / "sampled_2018_benign_api.csv").unlink()
    with pytest.raises(ValueError):
        data.list_data_files(tmp_path)


def test_list_data_files_empty_dir_raises(tmp_path):
    with pytest.raises(ValueError):
        data.list_data_files(tmp_path)


def test_load_year_combines_both_classes(tmp_path):
    make_dir(tmp_path, n_rows=6)
    df = data.load_year(2016, tmp_path)
    assert len(df) == 12
    assert set(df["year"]) == {2016}
    assert set(df["label"]) == {0, 1}
    assert (df["label"] == 1).sum() == 6 and (df["label"] == 0).sum() == 6
    assert "apkname" not in df.columns


# ---------- validate_feature_order / combine_years ----------

def _frame(tmp_path, year, cls, feats=FEATS, n=5):
    return data.load_file(make_csv(tmp_path / f"sampled_{year}_{cls}_api.csv", n_rows=n,
                                   seed=year, feats=feats))


def test_validate_feature_order_mismatched_order_raises(tmp_path):
    a = _frame(tmp_path, 2014, "malware")
    swapped = FEATS.copy()
    swapped[0], swapped[1] = swapped[1], swapped[0]
    b = _frame(tmp_path, 2015, "malware", feats=swapped)
    with pytest.raises(ValueError):
        data.validate_feature_order([a, b])


def test_validate_feature_order_mismatched_names_raises(tmp_path):
    a = _frame(tmp_path, 2014, "malware")
    renamed = FEATS.copy()
    renamed[5] = "other"
    b = _frame(tmp_path, 2015, "malware", feats=renamed)
    with pytest.raises(ValueError):
        data.validate_feature_order([a, b])


def test_validate_feature_order_ok(tmp_path):
    a = _frame(tmp_path, 2014, "malware")
    b = _frame(tmp_path, 2015, "malware")
    data.validate_feature_order([a, b])  # must not raise


def test_combine_years_row_count_and_columns(tmp_path):
    make_dir(tmp_path, years=(2014, 2015, 2016), n_rows=4)
    frames = {y: data.load_year(y, tmp_path) for y in (2014, 2015, 2016)}
    out = data.combine_years(frames)
    assert len(out) == sum(len(f) for f in frames.values()) == 24
    assert list(out.index) == list(range(24))
    assert set(out["year"]) == {2014, 2015, 2016}
    assert out.shape[1] == 1850
    # years appear in order
    assert list(out["year"]) == sorted(out["year"])


def test_combine_years_labels_balanced_per_year(tmp_path):
    make_dir(tmp_path, years=(2014, 2015), n_rows=4)
    out = data.combine_years({y: data.load_year(y, tmp_path) for y in (2014, 2015)})
    counts = out.groupby(["year", "label"]).size()
    assert (counts == 4).all()


def test_combine_years_mismatched_features_raises(tmp_path):
    f1 = _frame(tmp_path, 2014, "malware")
    swapped = FEATS[::-1]
    f2 = _frame(tmp_path, 2015, "malware", feats=swapped)
    with pytest.raises(ValueError):
        data.combine_years({2014: f1, 2015: f2})


def test_load_all_synthetic_end_to_end(tmp_path):
    d = tmp_path / "in"
    d.mkdir()
    make_dir(d, n_rows=3)
    df = data.load_all(d, use_cache=False)
    assert len(df) == 16 * 3
    assert sorted(df["year"].unique()) == list(ALL_YEARS)
    assert set(df["label"].unique()) == {0, 1}
    assert "apkname" not in df.columns
    assert not df.isna().any().any()


# ---------- cache ----------

def test_cache_key_changes_when_file_changes(tmp_path):
    make_dir(tmp_path, years=ALL_YEARS, n_rows=2)
    k1 = data.cache_key(tmp_path)
    assert data.cache_key(tmp_path) == k1  # stable
    p = tmp_path / "sampled_2014_malware_api.csv"
    with open(p, "a") as f:
        f.write("x," + ",".join(["0"] * N_FEAT) + "\n")  # size change
    assert data.cache_key(tmp_path) != k1


def test_cache_key_changes_with_mtime(tmp_path):
    import os
    make_dir(tmp_path, n_rows=2)
    k1 = data.cache_key(tmp_path)
    p = tmp_path / "sampled_2014_malware_api.csv"
    st = p.stat()
    os.utime(p, (st.st_atime, st.st_mtime + 100))
    assert data.cache_key(tmp_path) != k1


# ---------- train_duplicate_mask (Step 1 per PLAN) ----------

def test_train_duplicate_mask_flags_test_row_equal_to_train_row():
    cols = ["f0", "f1"]
    rows = [
        (1, 2, 2014), (3, 4, 2015),   # training
        (1, 2, 2017),                  # duplicate of a training row
        (9, 9, 2017),                  # unique
    ]
    df = pd.DataFrame(rows, columns=cols + ["year"]).astype({"f0": "int32", "f1": "int32"})
    df["label"] = 0
    mask = data.train_duplicate_mask(df, TRAIN_YEARS)
    assert len(mask) == len(df)
    assert bool(mask[2]) is True
    assert bool(mask[3]) is False


# ---------- real data ----------

def test_real_16_files_and_columns(real_data_dir):
    files = data.list_data_files(real_data_dir)
    assert len(files) == 16
    for p in files[:2]:
        header = pd.read_csv(p, nrows=0).columns
        assert len(header) == 1849
        assert header[0] == "apkname"


@pytest.mark.parametrize("year", [2014, 2019])
def test_real_year_sizes_labels_and_nan(real_data_dir, year):
    """Row counts follow AGENTS.md (verified): 9,000 per file for 2014-2018, 1,500 for
    2019-2021, so 18,000 / 3,000 per year. ASSIGNMENT.md's blanket 1,500 is wrong for
    2014-2018."""
    per_file = 9000 if year <= 2018 else 1500
    for cls, label in (("malware", 1), ("benign", 0)):
        df = data.load_file(real_data_dir / f"sampled_{year}_{cls}_api.csv")
        assert len(df) == per_file
        assert "apkname" not in df.columns
        assert set(df["label"].unique()) == {label}
        assert set(df["year"].unique()) == {year}
        assert not df.isna().any().any()
        assert len(data.feature_columns(df)) == 1848
    yr = data.load_year(year, real_data_dir)
    assert len(yr) == 2 * per_file
    assert (yr["label"] == 1).sum() == (yr["label"] == 0).sum() == per_file
    assert (yr[data.feature_columns(yr)].min().min()) >= 0
