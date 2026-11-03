"""Entry point: python -m src.main [--step N]."""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from src.config import RESULTS_DIR, TEST_YEARS, TRAIN_YEARS
from src.evaluate import (
    assert_test_years_only,
    baseline_accuracy,
    by_year_export,
    confusion_table,
    confusion_by_year,
    drift_summary,
    per_year_table,
    plot_by_year,
    pooled_table,
    save_table,
    sensitivity_tables,
    year_baseline_table,
)
from src.models import save_models, train_all_from_split, train_with_report
from src.preprocess import filter_report, prepare_split, split_table
from src.drift import run_drift_analysis
from src.sustainable import run_sustainable
from src.data import (
    _row_hashes,
    train_duplicate_mask,
    feature_columns,
    file_table,
    label_conflict_mask,
    load_all,
    summarize_data,
    write_data_summary,
)


def run_step1() -> pd.DataFrame:
    """Step 1: load and combine the data, write results/step1_*.csv|md, print a summary."""
    df = load_all()
    summary = summarize_data(df)
    write_data_summary(summary, RESULTS_DIR / "step1_data_summary")
    write_data_summary(file_table(df), RESULTS_DIR / "step1_file_table")
    n_features = len(feature_columns(df))
    print(f"Step 1: {len(df)} rows, {n_features} feature columns, memory {df.memory_usage().sum() / 1e6:.0f} MB")
    print(summary.to_string(index=False))
    # Feature vectors that occur with both labels anywhere in the data (all years pooled).
    hashes = _row_hashes(df)
    conflict = label_conflict_mask(hashes, df["label"].to_numpy())
    print(f"Label conflicts (all years pooled): {len(set(hashes[conflict]))} vectors, {int(conflict.sum())} rows")
    return df


def run_step2(df: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Step 2: KS feature drift and the concept-drift accuracy matrix; writes results/step2_*."""
    tables = run_drift_analysis(load_all() if df is None else df)
    for name in ("ks_vs_2014", "ks_consecutive", "accuracy_matrix"):
        print(f"Step 2 {name}:")
        print(tables[name].round(4).to_string())
    return tables


def run_step3(df: pd.DataFrame | None = None) -> dict:
    """Step 3: preprocess (fit on 2014-2016 only); writes results/step3_*."""
    df = load_all() if df is None else df
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    pre = split["preprocessor"]
    counts = filter_report(df, pre, TEST_YEARS)
    table = split_table(split)
    write_data_summary(counts, RESULTS_DIR / "step3_feature_counts")
    write_data_summary(table, RESULTS_DIR / "step3_split")
    write_data_summary(split["clip_stats"], RESULTS_DIR / "step3_clip")
    pd.Series(pre.kept_features_, name="feature").to_csv(RESULTS_DIR / "step3_kept_features.csv", index=False)
    print(f"Step 3: X_train {split['X_train'].shape} {split['X_train'].dtype}, X_test {split['X_test'].shape}")
    print(split["clip_stats"].to_string(index=False))
    print(counts.to_string(index=False))
    print(table.to_string(index=False))
    return split


def run_step4(split: dict | None = None) -> tuple[dict, pd.DataFrame]:
    """Step 4: train the three classifiers on 2014-2016; prints TRAINING-only sanity numbers.

    Returns (models, report) so Step 5 can reuse the fitted models instead of retraining.
    """
    split = prepare_split(load_all(), TRAIN_YEARS, TEST_YEARS) if split is None else split
    models, report = train_with_report(split)
    save_models(models)
    write_data_summary(report, RESULTS_DIR / "step4_training")
    print("Step 4 (training-set sanity check only, NOT evaluation):")
    print(report.to_string(index=False))
    return models, report


def test_duplicate_mask(df: pd.DataFrame, split: dict) -> np.ndarray:
    """Mask over the test rows of `split`: True where the exact feature vector also occurs in the training years.

    The mask is computed over all rows of df and then selected by year, so it lines up with split["X_test"] only if
    split_by_year kept df row order; this is asserted against the split's years and labels.
    """
    sel = df["year"].isin(TEST_YEARS).to_numpy()
    if not (np.array_equal(df.loc[sel, "year"].to_numpy(), split["years_test"])
            and np.array_equal(df.loc[sel, "label"].to_numpy(), split["y_test"])):
        raise ValueError("test rows of df are not aligned with the split's years_test/y_test")
    return train_duplicate_mask(df)[sel]


def run_step5(
    df: pd.DataFrame | None = None, split: dict | None = None, models: dict | None = None
) -> dict[str, pd.DataFrame]:
    """Step 5: evaluate the three classifiers on the pooled test years 2017-2021; writes results/step5_*.

    models: fitted Step 4 classifiers to reuse; trained on 2014-2016 here only when None (e.g. --step 5 alone).
    """
    df = load_all() if df is None else df
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS) if split is None else split
    if models is None:
        models = train_all_from_split(split)  # fit on 2014-2016 only
    X_test, y_test, years_test = split["X_test"], split["y_test"], split["years_test"]
    assert_test_years_only(years_test)
    main_table = pooled_table(models, X_test, y_test)
    base = baseline_accuracy(y_test)
    main_table["baseline_accuracy"] = base  # majority-class reference for the accuracy column
    dup_mask = test_duplicate_mask(df, split)
    no_dup, _ = sensitivity_tables(models, X_test, y_test, years_test, dup_mask)
    confusion = confusion_table(models, X_test, y_test)
    save_table(main_table, "step5_metrics")
    save_table(no_dup, "step5_pooled_no_dup")
    save_table(confusion, "step5_confusion")
    print(f"Step 5 (pooled test years, n={len(y_test)}; majority-class accuracy {base:.4f}):")
    print(main_table.round(4).to_string(index=False))
    base_nd = baseline_accuracy(y_test[~dup_mask])
    print(f"Sensitivity (no exact training duplicate; {int(dup_mask.sum())} test rows excluded; "
          f"majority-class accuracy of subset {base_nd:.4f}):")
    print(no_dup.round(4).to_string(index=False))
    print(confusion.to_string(index=False))
    return {"metrics": main_table, "no_dup": no_dup, "confusion": confusion}


def run_step6(
    df: pd.DataFrame | None = None, split: dict | None = None, models: dict | None = None
) -> dict[str, pd.DataFrame]:
    """Step 6: per-year evaluation of the three classifiers on 2017-2021; writes results/step6_*.

    models: fitted Step 4 classifiers to reuse; trained on 2014-2016 here only when None (e.g. --step 6 alone).
    Nothing is refit on a test year.
    """
    df = load_all() if df is None else df
    split = prepare_split(df, TRAIN_YEARS, TEST_YEARS) if split is None else split
    if models is None:
        models = train_all_from_split(split)  # fit on 2014-2016 only
    X_test, y_test, years_test = split["X_test"], split["y_test"], split["years_test"]
    assert_test_years_only(years_test)
    per_year = per_year_table(models, X_test, y_test, years_test)
    baseline = year_baseline_table(y_test, years_test)
    drift = drift_summary(per_year)
    # Guard: every test year for every classifier, i.e. 3 models x 5 years = 15 rows.
    if set(per_year["year"]) != set(TEST_YEARS) or len(per_year) != len(models) * len(TEST_YEARS):
        raise ValueError(f"per-year table has {len(per_year)} rows; expected {len(models)} models x {len(TEST_YEARS)} test years")
    # Sensitivity: only test rows with no exact duplicate in 2014-2016.
    dup_mask = test_duplicate_mask(df, split)
    _, per_year_nd = sensitivity_tables(models, X_test, y_test, years_test, dup_mask)
    save_table(by_year_export(per_year), "step6_by_year")
    save_table(baseline, "step6_baseline_by_year")
    save_table(drift, "step6_drift_summary")
    conf_year = confusion_by_year(models, X_test, y_test, years_test)
    save_table(per_year_nd.rename(columns={"model": "classifier"}), "step6_per_year_no_dup")
    save_table(conf_year, "step6_confusion_by_year")
    plot_by_year(per_year, RESULTS_DIR / "step6_by_year.png")
    print("Step 6 (per test year; malware = positive class):")
    print(by_year_export(per_year).round(4).to_string(index=False))
    print(baseline.round(4).to_string(index=False))
    print(drift.round(4).to_string(index=False))
    print("Confusion counts and predicted-malware share by year:")
    print(conf_year.round(4).to_string(index=False))
    out = {"by_year": per_year, "baseline": baseline, "drift": drift, "no_dup": per_year_nd, "confusion_by_year": conf_year}
    if "clip_by_year" in split:  # preprocessing extremes per year (measured before clipping in prepare_split)
        save_table(split["clip_by_year"], "step6_clip_by_year")
        print("Clip share and mean |z| by year (before clipping):")
        print(split["clip_by_year"].round(4).to_string(index=False))
        out["clip_by_year"] = split["clip_by_year"].query("side == 'test'")  # file keeps train rows as reference
    return out


def run_step7(
    df: pd.DataFrame | None = None, split: dict | None = None, models: dict | None = None,
    step4_report: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame]:
    """Step 7: static vs expanding vs sliding vs incremental on 2017-2021; writes results/step7_*.

    models/split: the Step 4 models and Step 3 split to reuse as the static baseline (built here when None).
    step4_report: Step 4 training table, used only for the static fit time.
    """
    df = load_all() if df is None else df
    if split is None:
        split = prepare_split(df, TRAIN_YEARS, TEST_YEARS)
    if models is None:
        models, step4_report = train_with_report(split)  # fit on 2014-2016 only
    seconds = dict(zip(step4_report["model"], step4_report["train_seconds"])) if step4_report is not None else None
    tables = run_sustainable(df, split, models, seconds)
    print("Step 7 (per test year; malware = positive class):")
    print(tables["strategies"][["strategy", "classifier", "year", "n", "accuracy", "precision", "recall", "f1"]].round(4).to_string(index=False))
    for name in ("summary", "pooled", "cost"):
        print(f"Step 7 {name}:")
        print(tables[name].round(4).to_string(index=False))
    return tables


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline (Steps 1-7); --step N runs one step."""
    parser = argparse.ArgumentParser(description="Project 2 pipeline")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="run a single step (1-7)")
    args = parser.parse_args(argv)
    df = run_step1()
    if args.step in (None, 2):
        run_step2(df)
    split = None
    if args.step in (None, 3):
        split = run_step3(df)
    models, report4 = None, None
    if args.step in (None, 4):
        models, report4 = run_step4(split)
    if args.step in (None, 5):
        run_step5(df, split, models)
    if args.step in (None, 6):
        run_step6(df, split, models)
    if args.step in (None, 7):
        run_step7(df, split, models, report4)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
