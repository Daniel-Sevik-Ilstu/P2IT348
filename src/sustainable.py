"""Step 7: sustainable approaches (static, expanding window, sliding window, incremental) on test years 2017-2021.

Rule for every strategy: year t is predicted before any of its rows is used to fit preprocessing or a model.
"""
from __future__ import annotations

import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning

from src.config import LABEL_COL, RESULTS_DIR, TEST_YEARS, TRAIN_YEARS, YEAR_COL
from src.data import feature_columns
from src.evaluate import compute_metrics, confusion_counts, save_table
from src.models import train_model
from src.preprocess import Preprocessor, check_no_overlap

STRATEGIES: tuple[str, ...] = ("static", "expanding", "sliding", "incremental")
WINDOW_SIZE: int = 3  # sliding window: the 3 years before the test year
EXPORT_COLUMNS: list[str] = ["strategy", "classifier", "year", "n", "accuracy", "precision", "recall", "f1"]
YearArrays = dict[int, tuple[np.ndarray, np.ndarray]]


def window_years(strategy: str, t: int) -> tuple[int, ...]:
    """Training years for `strategy` ("static", "expanding", "sliding") when predicting test year t.

    static: 2014-2016; expanding: 2014..t-1; sliding: t-3..t-1. Raises ValueError if t is not a test year, the
    strategy is unknown, or any returned year is >= t (the leakage guard shared by every Step 7 fit).
    """
    if t not in TEST_YEARS:
        raise ValueError(f"t={t} is not a test year {TEST_YEARS}")
    if strategy == "static":
        years = tuple(TRAIN_YEARS)
    elif strategy == "expanding":
        years = tuple(range(min(TRAIN_YEARS), t))
    elif strategy == "sliding":
        years = tuple(range(t - WINDOW_SIZE, t))
    else:
        raise ValueError(f"unknown window strategy {strategy!r}; expected static, expanding or sliding")
    if not years or max(years) >= t:
        raise ValueError(f"window {years} for {strategy} must be non-empty and precede test year {t}")
    return years


def check_years_present(df: pd.DataFrame) -> None:
    """Raise a ValueError naming any training or test year that has no rows in `df`."""
    missing = sorted((set(TRAIN_YEARS) | set(TEST_YEARS)) - set(df[YEAR_COL].unique().tolist()))
    if missing:
        raise ValueError(f"Step 7 needs data for years {sorted(set(TRAIN_YEARS) | set(TEST_YEARS))}; missing {missing}")


def year_arrays(df: pd.DataFrame) -> YearArrays:
    """Raw float32 feature matrix and labels per year, extracted once so windows only concatenate."""
    check_years_present(df)
    features = feature_columns(df)
    out: YearArrays = {}
    for year, g in df.groupby(YEAR_COL, sort=True):
        out[int(year)] = (g[features].to_numpy(dtype=np.float32), g[LABEL_COL].to_numpy())
    return out


def _stack(arrays: YearArrays, years: tuple[int, ...]) -> tuple[np.ndarray, np.ndarray]:
    """Concatenate the raw rows and labels of `years` (in the order given)."""
    return np.concatenate([arrays[y][0] for y in years]), np.concatenate([arrays[y][1] for y in years])


def fit_on_years(
    arrays: YearArrays, features: list[str], years: tuple[int, ...], t: int, model_name: str
) -> tuple[Preprocessor, Any, float, int, int]:
    """Fit a new Preprocessor and model on `years` only, after checking they all precede test year t.

    Every window fit goes through here (tests spy on it). Returns (preprocessor, model, seconds,
    n_training_rows, convergence_warnings); seconds covers preprocessing plus model fit.
    """
    check_no_overlap(years, [t])
    if max(years) >= t:  # belt and braces: check_no_overlap already enforces this
        raise AssertionError(f"training years {years} include a year >= {t}")
    X_raw, y = _stack(arrays, years)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        start = time.perf_counter()
        pre = Preprocessor().fit(X_raw, features)  # window rows only
        model = train_model(model_name, pre.transform(X_raw), y)
        seconds = time.perf_counter() - start
    n_conv = sum(issubclass(w.category, ConvergenceWarning) for w in caught)
    return pre, model, seconds, len(y), n_conv


def _result_row(
    strategy: str, classifier: str, t: int, y_true: np.ndarray, y_pred: np.ndarray,
    seconds: float, train_rows: int, years: tuple[int, ...], n_conv: int = 0,
) -> dict[str, Any]:
    """One result row: metrics, confusion counts, cost and the training window for one (strategy, classifier, year)."""
    return {"strategy": strategy, "classifier": classifier, "year": t, "n": len(y_true),
            **compute_metrics(y_true, y_pred), **confusion_counts(y_true, y_pred),
            "train_seconds": seconds, "train_rows": train_rows, "window": f"{min(years)}-{max(years)}",
            "convergence_warnings": n_conv}


def run_window_strategy(
    df: pd.DataFrame, strategy: str, model_name: str = "logreg", arrays: YearArrays | None = None
) -> pd.DataFrame:
    """Static, expanding or sliding strategy: for each test year t, fit on its window only, predict t.

    The static window is the same for every t, so it is fitted once (same result as refitting five times).
    Returns one row per test year.
    """
    arrays = year_arrays(df) if arrays is None else arrays
    features = feature_columns(df)
    rows, fitted = [], {}
    for t in TEST_YEARS:
        years = window_years(strategy, t)  # raises if any year >= t
        if strategy != "static" or years not in fitted:
            fitted[years] = fit_on_years(arrays, features, years, t, model_name)
        pre, model, seconds, n_rows, n_conv = fitted[years]
        X_t, y_t = arrays[t]
        pred = model.predict(pre.transform(X_t))  # year t is only transformed/predicted here
        # Static cost is paid once (first test year); later rows record 0 retraining seconds.
        paid = seconds if (strategy != "static" or t == TEST_YEARS[0]) else 0.0
        rows.append(_result_row(strategy, model_name, t, y_t, pred, paid, n_rows, years, n_conv))
    return pd.DataFrame(rows)


def run_incremental(df: pd.DataFrame, model_name: str = "sgd", arrays: YearArrays | None = None) -> pd.DataFrame:
    """Incremental test-then-train: fit on 2014-2016, then for each t predict t and only afterwards `partial_fit` on t.

    The preprocessor (zero-column mask, scaler) is fitted on 2014-2016 and frozen, so year t never influences it.
    train_seconds of a row is the cost of the update that produced the model used for that row's prediction
    (2017: the initial fit; later years: the partial_fit on the previous year).
    """
    arrays = year_arrays(df) if arrays is None else arrays
    features = feature_columns(df)
    pre, model, seconds, n_rows, n_conv = fit_on_years(arrays, features, tuple(TRAIN_YEARS), TEST_YEARS[0], model_name)
    seen = list(TRAIN_YEARS)
    rows = []
    for t in TEST_YEARS:
        if max(seen) >= t:  # every year used so far must precede the year being predicted
            raise AssertionError(f"incremental model has seen {seen}, which includes a year >= {t}")
        X_t, y_t = arrays[t]
        Z_t = pre.transform(X_t)  # frozen preprocessor: transform only
        pred = model.predict(Z_t)  # 1) predict t ...
        rows.append(_result_row("incremental", model_name, t, y_t, pred, seconds, n_rows, tuple(seen), n_conv))
        start = time.perf_counter()
        model.partial_fit(Z_t, y_t)  # 2) ... then learn from t (labels arrive after the year ends)
        seconds, n_rows, n_conv = time.perf_counter() - start, len(y_t), 0
        seen.append(t)
    return pd.DataFrame(rows)


def static_from_models(
    split: dict, models: dict[str, Any], train_seconds: dict[str, float] | None = None,
    arrays: YearArrays | None = None,
) -> pd.DataFrame:
    """Static rows from the already fitted Step 4 models (nothing is refitted). train_seconds: Step 4 fit times.

    Raises ValueError if the split's training years are not exactly TRAIN_YEARS, or (when `arrays` is given) if the
    split's test labels of a year differ from the labels the other strategies score (`arrays[t][1]`).
    """
    years_train = tuple(sorted(set(split["years_train"].tolist())))
    if years_train != tuple(TRAIN_YEARS):
        raise ValueError(f"static split must be trained on exactly {tuple(TRAIN_YEARS)}, got {years_train}")
    if arrays is not None:  # same test rows as every other strategy
        for t in TEST_YEARS:
            if not np.array_equal(split["y_test"][split["years_test"] == t], arrays[t][1]):
                raise ValueError(f"static test labels for {t} differ from the labels used by the other strategies")
    rows = []
    for name, model in models.items():
        pred = model.predict(split["X_test"])
        for t in TEST_YEARS:
            sel = split["years_test"] == t
            secs = (train_seconds or {}).get(name, float("nan")) if t == TEST_YEARS[0] else 0.0
            rows.append(_result_row("static", name, t, split["y_test"][sel], pred[sel], secs, len(split["y_train"]), years_train))
    return pd.DataFrame(rows)


def run_all_strategies(
    df: pd.DataFrame,
    split: dict | None = None,
    models: dict[str, Any] | None = None,
    step4_seconds: dict[str, float] | None = None,
    rf: bool = True,
) -> pd.DataFrame:
    """Run (a)-(d) for logreg and SGD, plus static and expanding for random forest (rf=True).

    split/models: Step 4 split and fitted models; if both are given the static rows come from those models.
    Returns one row per (strategy, classifier, test year).
    """
    arrays = year_arrays(df)
    parts = []
    plan = {"logreg": ("static", "expanding", "sliding"), "sgd": ("static", "expanding", "sliding", "incremental")}
    if rf:
        plan["random_forest"] = ("static", "expanding")
    for name, strategies in plan.items():
        for strategy in strategies:
            if strategy == "static" and split is not None and models is not None and name in models:
                parts.append(static_from_models(split, {name: models[name]}, step4_seconds, arrays))
            elif strategy == "incremental":
                parts.append(run_incremental(df, name, arrays))
            else:
                parts.append(run_window_strategy(df, strategy, name, arrays))
    return pd.concat(parts, ignore_index=True)


def pooled_by_strategy(results: pd.DataFrame) -> pd.DataFrame:
    """Metrics pooled over all test years per (strategy, classifier), from the summed confusion counts.

    Years are weighted by size (2017-2018 have 6x the rows of 2019-2021), so the per-year table is the main view.
    """
    rows = []
    for (strategy, clf), g in results.groupby(["strategy", "classifier"], sort=False):
        tn, fp, fn, tp = (int(g[c].sum()) for c in ("tn", "fp", "fn", "tp"))
        n = tn + fp + fn + tp
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        rows.append({"strategy": strategy, "classifier": clf, "n": n, "accuracy": (tp + tn) / n,
                     "precision": prec, "recall": rec, "f1": f1})
    return pd.DataFrame(rows)


def compare_to_static(results: pd.DataFrame) -> pd.DataFrame:
    """Per (strategy, classifier, year): F1 and accuracy minus the static model of the same classifier."""
    static = results[results["strategy"] == "static"].set_index(["classifier", "year"])
    out = results[["strategy", "classifier", "year", "f1", "accuracy"]].copy()
    key = list(zip(out["classifier"], out["year"]))
    out["f1_static"] = [static["f1"].get(k, np.nan) for k in key]
    out["accuracy_static"] = [static["accuracy"].get(k, np.nan) for k in key]
    out["f1_diff"] = out["f1"] - out["f1_static"]
    out["accuracy_diff"] = out["accuracy"] - out["accuracy_static"]
    return out[out["strategy"] != "static"].reset_index(drop=True)


def summary_table(results: pd.DataFrame) -> pd.DataFrame:
    """Per (strategy, classifier): mean F1 over the 5 test years (unweighted), worst year, 2019-2021 means, gain over static."""
    rows = []
    for (strategy, clf), g in results.groupby(["strategy", "classifier"], sort=False):
        worst = g.loc[g["f1"].idxmin()]
        late = g[g["year"] >= 2019]
        rows.append({"strategy": strategy, "classifier": clf, "mean_f1": g["f1"].mean(), "worst_f1": worst["f1"],
                     "worst_year": int(worst["year"]), "mean_f1_2019_21": late["f1"].mean(),
                     "mean_accuracy_2019_21": late["accuracy"].mean(), "mean_accuracy": g["accuracy"].mean()})
    out = pd.DataFrame(rows)
    base = out[out["strategy"] == "static"].set_index("classifier")
    out["mean_f1_gain_vs_static"] = out["mean_f1"] - out["classifier"].map(base["mean_f1"])
    out["mean_acc_2019_21_gain_vs_static"] = out["mean_accuracy_2019_21"] - out["classifier"].map(base["mean_accuracy_2019_21"])
    return out


def cost_table(results: pd.DataFrame) -> pd.DataFrame:
    """Training cost per (strategy, classifier): number of fits/updates, total and mean seconds, mean training rows."""
    rows = []
    for (strategy, clf), g in results.groupby(["strategy", "classifier"], sort=False):
        if strategy == "static":
            secs = g["train_seconds"].iloc[:1]  # one fit, paid once
        else:
            secs = g["train_seconds"]
        rows.append({"strategy": strategy, "classifier": clf, "n_fits": len(secs), "total_seconds": secs.sum(min_count=1),  # NaN (not 0.0) when the seconds are unknown
                     "mean_seconds_per_update": secs.mean(), "max_seconds": secs.max(),
                     "mean_train_rows": g["train_rows"].mean()})
    return pd.DataFrame(rows)


def window_composition(df: pd.DataFrame) -> pd.DataFrame:
    """Rows per year in the training data behind each prediction, for every strategy and test year.

    The incremental model has seen the same years as the expanding window (2014..t-1) but through the single
    pass of `partial_fit`; its preprocessor only ever saw 2014-2016.
    """
    check_years_present(df)
    counts = df.groupby(YEAR_COL).size()
    rows = []
    for strategy in STRATEGIES:
        for t in TEST_YEARS:
            years = window_years("expanding" if strategy == "incremental" else strategy, t)
            total = int(sum(counts[y] for y in years))
            row = {"strategy": strategy, "test_year": t, "window": f"{min(years)}-{max(years)}", "train_rows": total}
            row.update({f"n_{y}": int(counts[y]) if y in years else 0 for y in sorted(counts.index)})
            row["share_2014_2018"] = sum(int(counts[y]) for y in years if y <= 2018) / total
            row["share_last_year"] = int(counts[max(years)]) / total
            rows.append(row)
    return pd.DataFrame(rows)


def plot_strategies(results: pd.DataFrame, path: Path) -> None:
    """Save F1 (top) and accuracy (bottom) by test year, one panel per classifier, one line per strategy.

    Dashed lines: F1 of always predicting malware on a balanced year (2*0.5/(0.5+1) = 0.667) and accuracy 0.5.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    clfs = list(dict.fromkeys(results["classifier"]))
    fig, axes = plt.subplots(2, len(clfs), figsize=(4.5 * len(clfs), 7), sharex=True, squeeze=False)
    for j, clf in enumerate(clfs):
        for i, (metric, chance, label) in enumerate((("f1", 2 / 3, "always-malware F1 = 0.667"), ("accuracy", 0.5, "chance accuracy = 0.5"))):
            ax = axes[i][j]
            for strategy, g in results[results["classifier"] == clf].groupby("strategy", sort=False):
                g = g.sort_values("year")
                ax.plot(g["year"], g[metric], marker="o", label=strategy)
            ax.axhline(chance, ls="--", color="gray", label=label)
            ax.set_title(f"{clf}: {metric} by test year")
            ax.set_xticks(list(TEST_YEARS))
            ax.grid(alpha=0.3)
            ax.legend(fontsize=7)
            if j == 0:
                ax.set_ylabel(f"{metric} (malware = positive class)")
        axes[1][j].set_xlabel("test year")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run_sustainable(
    df: pd.DataFrame,
    split: dict | None = None,
    models: dict[str, Any] | None = None,
    step4_seconds: dict[str, float] | None = None,
    rf: bool = True,
) -> dict[str, pd.DataFrame]:
    """Run all strategies, write results/step7_* (strategies, pooled, vs_static, summary, cost, window_composition, png)."""
    results = run_all_strategies(df, split, models, step4_seconds, rf)
    tables = {
        "strategies": results,
        "pooled": pooled_by_strategy(results),
        "vs_static": compare_to_static(results),
        "summary": summary_table(results),
        "cost": cost_table(results),
        "window_composition": window_composition(df),
    }
    save_table(results[EXPORT_COLUMNS], "step7_strategies")
    save_table(results, "step7_strategies_detail")  # + confusion counts, cost, window
    for name in ("pooled", "vs_static", "summary", "cost", "window_composition"):
        save_table(tables[name], f"step7_{name}")
    plot_strategies(results, RESULTS_DIR / "step7_f1_by_year.png")
    return tables
