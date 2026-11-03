"""Entry point: python -m src.main [--step N]."""
from __future__ import annotations

import argparse
import sys

import pandas as pd

from src.config import RESULTS_DIR, TEST_YEARS, TRAIN_YEARS
from src.preprocess import filter_report, prepare_split, split_table
from src.drift import run_drift_analysis
from src.data import (
    _row_hashes,
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


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline (Steps 1-3 exist so far); --step N runs one step."""
    parser = argparse.ArgumentParser(description="Project 2 pipeline")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="run a single step (1-7)")
    args = parser.parse_args(argv)
    if args.step not in (None, 1, 2, 3):
        print(f"Step {args.step} is not implemented yet.", file=sys.stderr)
        return 1  # non-zero so callers can tell nothing ran
    df = run_step1() if args.step in (None, 1, 2, 3) else None
    if args.step in (None, 2):
        run_step2(df)
    if args.step in (None, 3):
        run_step3(df)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
