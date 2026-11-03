"""Entry point: python -m src.main [--step N]."""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from src.config import RESULTS_DIR, TEST_YEARS, TRAIN_YEARS
from src.evaluate import (
    assert_test_years_only,
    baseline_accuracy,
    confusion_table,
    pooled_table,
    save_table,
    sensitivity_tables,
)
from src.models import save_models, train_all_from_split, train_with_report
from src.preprocess import filter_report, prepare_split, split_table
from src.drift import run_drift_analysis
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
    # Mask over all rows of df; select the test rows (split_by_year keeps df order).
    dup_mask = train_duplicate_mask(df)[df["year"].isin(TEST_YEARS).to_numpy()]
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


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline (Steps 1-5 exist so far); --step N runs one step."""
    parser = argparse.ArgumentParser(description="Project 2 pipeline")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="run a single step (1-7)")
    args = parser.parse_args(argv)
    if args.step not in (None, 1, 2, 3, 4, 5):
        print(f"Step {args.step} is not implemented yet.", file=sys.stderr)
        return 1  # non-zero so callers can tell nothing ran
    df = run_step1()
    if args.step in (None, 2):
        run_step2(df)
    split = None
    if args.step in (None, 3):
        split = run_step3(df)
    models = None
    if args.step in (None, 4):
        models, _ = run_step4(split)
    if args.step in (None, 5):
        run_step5(df, split, models)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
