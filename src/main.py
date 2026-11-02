"""Entry point: python -m src.main [--step N]."""
from __future__ import annotations

import argparse

import pandas as pd

from src.config import RESULTS_DIR
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
    n_features = df.shape[1] - 2  # minus label and year
    print(f"Step 1: {len(df)} rows, {n_features} feature columns, memory {df.memory_usage().sum() / 1e6:.0f} MB")
    print(summary.to_string(index=False))
    # Feature vectors that occur with both labels anywhere in the data (all years pooled).
    hashes = _row_hashes(df)
    conflict = label_conflict_mask(hashes, df["label"].to_numpy())
    print(f"Label conflicts (all years pooled): {len(set(hashes[conflict]))} vectors, {int(conflict.sum())} rows")
    return df


def main(argv: list[str] | None = None) -> int:
    """Run the pipeline (only Step 1 exists so far); --step N runs one step."""
    parser = argparse.ArgumentParser(description="Project 2 pipeline")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="run a single step (1-7)")
    args = parser.parse_args(argv)
    if args.step in (None, 1):
        run_step1()
    if args.step not in (None, 1):
        print(f"Step {args.step} is not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
