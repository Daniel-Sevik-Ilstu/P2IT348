"""Step 2: measure feature drift (KS tests) and concept drift (train-on-i / test-on-j accuracy).

Diagnostic only: nothing here feeds Steps 3-7, so it is exempt from the train-2014-2016 rule
(see PLAN.md section 0).
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display needed
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from src.config import ALL_YEARS, LABEL_COL, RESULTS_DIR, SEED, YEAR_COL
from src.data import feature_columns


def subsample_years(df: pd.DataFrame, n: int | None = None, seed: int = SEED) -> dict[int, pd.DataFrame]:
    """Return an equal-size, class-balanced random sample of n rows per year (n=None: smallest year)."""
    years = sorted(df[YEAR_COL].unique())
    if n is None:
        n = int(min((df[YEAR_COL] == y).sum() for y in years))
    half = n // 2
    out: dict[int, pd.DataFrame] = {}
    for y in years:
        parts = []
        for label in (0, 1):
            rows = df[(df[YEAR_COL] == y) & (df[LABEL_COL] == label)]
            if len(rows) < half:
                raise ValueError(f"year {y} class {label} has {len(rows)} rows, need {half}")
            parts.append(rows.sample(n=half, random_state=seed))
        out[int(y)] = pd.concat(parts).reset_index(drop=True)
    return out


def ks_feature_table(a: pd.DataFrame, b: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    """Run ks_2samp on each feature; features constant with the same value in both samples are skipped."""
    xa = a[features].to_numpy()
    xb = b[features].to_numpy()
    stat = np.full(len(features), np.nan)
    pval = np.full(len(features), np.nan)
    skipped = np.zeros(len(features), dtype=bool)
    for k in range(len(features)):
        ca, cb = xa[:, k], xb[:, k]
        # Constant in both samples with the same value: nothing to compare.
        if ca.min() == ca.max() and cb.min() == cb.max() and ca[0] == cb[0]:
            skipped[k] = True
            continue
        res = ks_2samp(ca, cb, method="asymp")  # exact method fails on heavily tied counts
        stat[k], pval[k] = res.statistic, res.pvalue
    tested = ~skipped
    if np.isnan(stat[tested]).any() or np.isnan(pval[tested]).any():
        raise ValueError("KS produced NaN for a tested feature")
    return pd.DataFrame({"feature": features, "ks_stat": stat, "p_value": pval, "skipped": skipped})


def bonferroni_significant(p_values: np.ndarray, alpha: float = 0.05) -> np.ndarray:
    """Boolean mask p < alpha / m, with m the number of tested (non-NaN) p-values; NaN is never significant."""
    p = np.asarray(p_values, dtype=float)
    m = int((~np.isnan(p)).sum())
    if m == 0:
        return np.zeros(p.shape, dtype=bool)
    with np.errstate(invalid="ignore"):
        return p < alpha / m


def ks_all_pairs(samples: dict[int, pd.DataFrame], features: list[str]) -> dict[tuple[int, int], pd.DataFrame]:
    """KS feature table for every year pair (a < b); the other tables are views on this dict."""
    return {(a, b): ks_feature_table(samples[a], samples[b], features) for a, b in combinations(sorted(samples), 2)}


def _pair_row(a: int, b: int, table: pd.DataFrame) -> dict:
    """Summary of one pair's feature table: tested/skipped counts, mean KS, % Bonferroni-significant."""
    tested = ~table["skipped"].to_numpy()
    sig = bonferroni_significant(table["p_value"].to_numpy())
    return {
        "year_a": a,
        "year_b": b,
        "n_tested": int(tested.sum()),
        "n_skipped": int((~tested).sum()),
        "mean_ks": float(table.loc[tested, "ks_stat"].mean()),
        "share_significant": float(sig.sum() / max(tested.sum(), 1)),
    }


def ks_year_pairs(pairs: dict[tuple[int, int], pd.DataFrame], mode: str) -> pd.DataFrame:
    """One summary row per pair: mode 'vs_2014', 'consecutive' or 'all' (every pair)."""
    if mode == "vs_2014":
        keys = [k for k in pairs if k[0] == min(ALL_YEARS)]
    elif mode == "consecutive":
        keys = [k for k in pairs if k[1] - k[0] == 1]
    elif mode == "all":
        keys = list(pairs)
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return pd.DataFrame([_pair_row(a, b, pairs[(a, b)]) for a, b in sorted(keys)])


def ks_matrix(pair_table: pd.DataFrame, years: list[int], value: str = "mean_ks") -> pd.DataFrame:
    """Symmetric year x year matrix of a pair-table column (diagonal 0)."""
    m = pd.DataFrame(0.0, index=years, columns=years)
    for _, r in pair_table.iterrows():
        m.loc[int(r.year_a), int(r.year_b)] = m.loc[int(r.year_b), int(r.year_a)] = r[value]
    return m


def most_different_years(pair_table: pd.DataFrame) -> pd.DataFrame:
    """Pairs ranked by mean KS, largest first."""
    return pair_table.sort_values("mean_ks", ascending=False).reset_index(drop=True)


def top_drifting_features(
    pairs: dict[tuple[int, int], pd.DataFrame],
    samples: dict[int, pd.DataFrame],
    features: list[str],
    k: int = 20,
) -> pd.DataFrame:
    """Top-k features by mean KS over the 'vs 2014' comparisons, with per-year KS and per-year means."""
    base = min(samples)
    later = [y for y in sorted(samples) if y != base]
    out = pd.DataFrame({"feature": features})
    for y in later:
        out[f"ks_{y}"] = pairs[(base, y)]["ks_stat"].to_numpy()
    out["mean_ks"] = out[[f"ks_{y}" for y in later]].mean(axis=1)  # NaN rows (skipped everywhere) sort last
    for y in sorted(samples):
        out[f"mean_{y}"] = samples[y][features].to_numpy().mean(axis=0)
    return out.sort_values("mean_ks", ascending=False).head(k).reset_index(drop=True)


def concept_drift_matrix(samples: dict[int, pd.DataFrame], features: list[str], seed: int = SEED) -> pd.DataFrame:
    """Accuracy matrix: rows = training year i, columns = test year j.

    Per year i: log1p + StandardScaler + LogisticRegression, all fit on year i's training part only.
    The diagonal uses a stratified 70/30 split of year i (accuracy on the held-out 30%); off-diagonal
    cells use the whole sample of year j.
    """
    years = sorted(samples)
    acc = pd.DataFrame(np.nan, index=years, columns=years)
    for i in years:
        x = np.log1p(samples[i][features].to_numpy(dtype=np.float64))
        y = samples[i][LABEL_COL].to_numpy()
        x_tr, x_ho, y_tr, y_ho = train_test_split(x, y, test_size=0.3, stratify=y, random_state=seed)
        # Scaler and model see year i's training rows only.
        scaler = StandardScaler().fit(x_tr)
        model = LogisticRegression(max_iter=1000, random_state=seed).fit(scaler.transform(x_tr), y_tr)
        for j in years:
            if j == i:
                acc.loc[i, j] = accuracy_score(y_ho, model.predict(scaler.transform(x_ho)))
            else:
                xj = np.log1p(samples[j][features].to_numpy(dtype=np.float64))
                acc.loc[i, j] = accuracy_score(samples[j][LABEL_COL].to_numpy(), model.predict(scaler.transform(xj)))
    return acc


def _save_heatmap(matrix: pd.DataFrame, path: Path, title: str, cbar_label: str) -> None:
    """Save a year x year matrix as an annotated heatmap PNG."""
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(matrix.to_numpy(dtype=float), cmap="viridis")
    ax.set_xticks(range(len(matrix.columns)), [str(c) for c in matrix.columns])
    ax.set_yticks(range(len(matrix.index)), [str(i) for i in matrix.index])
    for r in range(matrix.shape[0]):
        for c in range(matrix.shape[1]):
            ax.text(c, r, f"{matrix.iat[r, c]:.2f}", ha="center", va="center", color="white", fontsize=8)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=cbar_label)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def run_drift_analysis(df: pd.DataFrame, results_dir: Path = RESULTS_DIR) -> dict[str, pd.DataFrame]:
    """Run all Step 2 analyses, write results/step2_*.csv|png, and return the tables."""
    results_dir.mkdir(parents=True, exist_ok=True)
    features = feature_columns(df)
    samples = subsample_years(df)
    years = sorted(samples)
    pairs = ks_all_pairs(samples, features)
    all_pairs = ks_year_pairs(pairs, "all")
    tables = {
        "ks_vs_2014": ks_year_pairs(pairs, "vs_2014"),
        "ks_consecutive": ks_year_pairs(pairs, "consecutive"),
        "ks_all_pairs": most_different_years(all_pairs),
        "ks_matrix": ks_matrix(all_pairs, years),
        "top20_features": top_drifting_features(pairs, samples, features, 20),
        "accuracy_matrix": concept_drift_matrix(samples, features),
    }
    for name, t in tables.items():
        # The two matrices are indexed by year; keep the index as a column.
        t.to_csv(results_dir / f"step2_{name}.csv", index=name.endswith("matrix"), index_label="year")
    _save_heatmap(tables["ks_matrix"], results_dir / "step2_ks_matrix.png", "Mean KS statistic between years", "mean KS")
    _save_heatmap(tables["accuracy_matrix"], results_dir / "step2_accuracy_matrix.png",
                  "Accuracy: train year (row) -> test year (column)", "accuracy")
    return tables
