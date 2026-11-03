"""Steps 5 and 6: evaluate the trained classifiers on the held-out test years (malware = positive class)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score

from src.config import RESULTS_DIR, TEST_YEARS
from src.data import write_data_summary

METRIC_NAMES: tuple[str, ...] = ("accuracy", "precision", "recall", "f1")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Accuracy, precision, recall and F1 with malware (label 1) as the positive class."""
    kwargs = {"pos_label": 1, "zero_division": 0}  # zero_division=0: no predicted/actual malware gives 0, not an error
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, **kwargs)),
        "recall": float(recall_score(y_true, y_pred, **kwargs)),
        "f1": float(f1_score(y_true, y_pred, **kwargs)),
    }


def confusion_counts(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    """Confusion matrix as TN, FP, FN, TP counts (labels fixed to [0, 1] so a missing class still gives 2x2)."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


def assert_test_years_only(years: np.ndarray) -> None:
    """Raise ValueError if any year is outside TEST_YEARS (metrics must never be computed on training years)."""
    bad = sorted(set(np.unique(years).tolist()) - set(TEST_YEARS))
    if bad:
        raise ValueError(f"evaluation data contains years outside {TEST_YEARS}: {bad}")


def _check_same_length(X_test: np.ndarray, y_test: np.ndarray) -> None:
    """Raise ValueError if X_test and y_test have different numbers of rows."""
    if len(X_test) != len(y_test):
        raise ValueError(f"X_test has {len(X_test)} rows but y_test has {len(y_test)}")


def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> dict[str, float]:
    """Predict with a fitted model and return its four metrics."""
    return compute_metrics(y_test, model.predict(X_test))


def pooled_table(models: dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> pd.DataFrame:
    """One row per classifier: model, accuracy, precision, recall, f1, n_test (pooled over the test years)."""
    _check_same_length(X_test, y_test)
    rows = [{"model": name, **evaluate_model(m, X_test, y_test), "n_test": len(y_test)} for name, m in models.items()]
    return pd.DataFrame(rows, columns=["model", *METRIC_NAMES, "n_test"])


def per_year_table(
    models: dict[str, Any], X_test: np.ndarray, y_test: np.ndarray, years_test: np.ndarray
) -> pd.DataFrame:
    """One row per (model, test year): metrics plus year and n."""
    assert_test_years_only(years_test)
    rows = []
    for name, m in models.items():
        pred = m.predict(X_test)  # predict once, slice per year
        for year in sorted(set(years_test.tolist())):
            sel = years_test == year
            rows.append({"model": name, "year": int(year), **compute_metrics(y_test[sel], pred[sel]), "n": int(sel.sum())})
    return pd.DataFrame(rows, columns=["model", "year", *METRIC_NAMES, "n"])


def drift_summary(per_year: pd.DataFrame) -> pd.DataFrame:
    """Per model: F1 in the first and last test year, the drop between them, and the least-squares F1 slope per year."""
    rows = []
    for name, g in per_year.groupby("model", sort=False):
        g = g.sort_values("year")
        first, last = float(g["f1"].iloc[0]), float(g["f1"].iloc[-1])
        slope = float(np.polyfit(g["year"].to_numpy(dtype=float), g["f1"].to_numpy(dtype=float), 1)[0]) if len(g) > 1 else 0.0
        rows.append({"model": name, "first_year": int(g["year"].iloc[0]), "last_year": int(g["year"].iloc[-1]),
                     "f1_first": first, "f1_last": last, "f1_drop": first - last, "f1_slope_per_year": slope})
    return pd.DataFrame(rows)


def year_baseline_table(y_test: np.ndarray, years_test: np.ndarray) -> pd.DataFrame:
    """Per test year: n, malware/benign counts, malware share and majority-class (baseline) accuracy."""
    assert_test_years_only(years_test)
    rows = []
    for year in sorted(set(years_test.tolist())):
        y = y_test[years_test == year]
        rows.append({"year": int(year), "n": len(y), "n_malware": int((y == 1).sum()), "n_benign": int((y == 0).sum()),
                     "malware_share": float(np.mean(y == 1)), "baseline_accuracy": baseline_accuracy(y)})
    return pd.DataFrame(rows)


def confusion_by_year(
    models: dict[str, Any], X_test: np.ndarray, y_test: np.ndarray, years_test: np.ndarray
) -> pd.DataFrame:
    """One row per (classifier, test year): tn, fp, fn, tp and the share of rows predicted as malware."""
    assert_test_years_only(years_test)
    rows = []
    for name, m in models.items():
        pred = m.predict(X_test)  # predict once, slice per year
        for year in sorted(set(years_test.tolist())):
            sel = years_test == year
            rows.append({"classifier": name, "year": int(year), **confusion_counts(y_test[sel], pred[sel]),
                         "predicted_malware_share": float(np.mean(pred[sel] == 1))})
    return pd.DataFrame(rows)


def by_year_export(per_year: pd.DataFrame) -> pd.DataFrame:
    """Step 6 file layout: columns classifier, year, n, accuracy, precision, recall, f1."""
    out = per_year.rename(columns={"model": "classifier"})
    return out[["classifier", "year", "n", *METRIC_NAMES]]


def plot_by_year(per_year: pd.DataFrame, path: Path) -> None:
    """Save a two-panel figure (F1 and accuracy by test year, one line per classifier) to path."""
    import matplotlib

    matplotlib.use("Agg")  # no display needed
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharex=True)
    for ax, metric in zip(axes, ("f1", "accuracy")):
        for name, g in per_year.groupby("model", sort=False):
            g = g.sort_values("year")
            ax.plot(g["year"], g[metric], marker="o", label=name)
        ax.set_title(f"{metric.upper() if metric == 'f1' else metric.capitalize()} by test year")
        ax.set_xlabel("test year")
        ax.set_xticks(sorted(per_year["year"].unique()))
        ax.grid(alpha=0.3)
    axes[0].set_ylabel("score (malware = positive class)")
    axes[0].legend()
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def confusion_table(models: dict[str, Any], X_test: np.ndarray, y_test: np.ndarray) -> pd.DataFrame:
    """One row per classifier with pooled tn, fp, fn, tp counts."""
    _check_same_length(X_test, y_test)
    return pd.DataFrame([{"model": n, **confusion_counts(y_test, m.predict(X_test))} for n, m in models.items()])


def baseline_accuracy(y_test: np.ndarray) -> float:
    """Accuracy of always predicting the majority class of y_test."""
    return float(max(np.mean(y_test == 1), np.mean(y_test == 0)))


def sensitivity_tables(
    models: dict[str, Any], X_test: np.ndarray, y_test: np.ndarray, years_test: np.ndarray, dup_mask: np.ndarray
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pooled and per-year tables on test rows with NO exact duplicate in the training years (dup_mask False).

    Each table gets an n_excluded column (rows removed by the filter; per year for the per-year table).
    The pooled table also gets n_malware/n_benign (kept) and n_excluded_malware/n_excluded_benign, so the
    change in class mix caused by the filter is visible.
    """
    dup_mask = np.asarray(dup_mask, dtype=bool)
    if len(dup_mask) != len(y_test):
        raise ValueError(f"dup_mask has {len(dup_mask)} entries but there are {len(y_test)} test rows")
    keep = ~dup_mask
    if keep.sum() == 0:
        raise ValueError("every test row has an exact duplicate in the training years; nothing left to evaluate")
    pooled = pooled_table(models, X_test[keep], y_test[keep])
    pooled["n_excluded"] = int(dup_mask.sum())
    # Class counts kept and removed (label 1 = malware, 0 = benign).
    pooled["n_malware"] = int((y_test[keep] == 1).sum())
    pooled["n_benign"] = int((y_test[keep] == 0).sum())
    pooled["n_excluded_malware"] = int((y_test[dup_mask] == 1).sum())
    pooled["n_excluded_benign"] = int((y_test[dup_mask] == 0).sum())
    per_year = per_year_table(models, X_test[keep], y_test[keep], years_test[keep])
    excluded = pd.Series(years_test[dup_mask]).value_counts()
    per_year["n_excluded"] = per_year["year"].map(lambda y: int(excluded.get(y, 0)))
    return pooled, per_year


def save_table(df: pd.DataFrame, stem: str) -> None:
    """Write results/<stem>.csv and results/<stem>.md (floats rounded to 4 decimals in both)."""
    write_data_summary(df.round(4), RESULTS_DIR / stem)
